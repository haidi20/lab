import unittest
from datetime import datetime

from modules.inaproc.api.collector import Collector, JobState
from modules.inaproc.api.auth import AuthError
from modules.inaproc.api.db import DbUnavailableError
from modules.inaproc.api.scraper import ScrapeResult
from modules.inaproc.api.spt import SptNumber

SAMPLE = SptNumber.parse("11469/SJ-IND.8/E-TKDN/7/2025")


class FakeStore:
    def __init__(self, final_numbers=None):
        self.final = set(final_numbers or [])
        self.rows_written = {}
        self.checks = {}
        self.deleted = []

    def is_final(self, number):
        return number in self.final

    def upsert_rows(self, number, rows, fetched_at):
        self.rows_written[number] = rows

    def delete_rows_for_number(self, number):
        self.deleted.append(number)

    def upsert_check(self, number, status, error_msg, checked_at):
        self.checks[number] = (status, error_msg)


class FakeScraper:
    def __init__(self, results=None, fail_on=None, error=None):
        self.results = results or {}
        self.fail_on = fail_on or set()
        self.error = error
        self.calls = []

    def fetch(self, number):
        key = str(number)
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        if key in self.fail_on:
            raise RuntimeError("scrape failed")
        return self.results.get(key, ScrapeResult(status="empty", rows=[]))


class CollectorTest(unittest.TestCase):
    def test_loop_rentang(self):
        store = FakeStore()
        scraper = FakeScraper()
        collector = Collector(store, scraper, sleep=lambda _: None)
        job = collector.collect(SAMPLE, 1000, 1002)
        self.assertEqual(job.status, "done")
        self.assertEqual(job.total, 3)
        self.assertEqual(len(scraper.calls), 3)

    def test_skip_cache_final(self):
        number = str(SAMPLE.with_sequence(1000))
        store = FakeStore(final_numbers=[number])
        scraper = FakeScraper()
        collector = Collector(store, scraper, sleep=lambda _: None)
        job = collector.collect(SAMPLE, 1000, 1001)
        self.assertEqual(scraper.calls, [str(SAMPLE.with_sequence(1001))])
        self.assertEqual(job.skipped, 1)

    def test_force_memproses_ulang_nomor_final(self):
        number = str(SAMPLE.with_sequence(1000))
        store = FakeStore(final_numbers=[number])
        scraper = FakeScraper()
        collector = Collector(store, scraper, sleep=lambda _: None)
        job = collector.collect(SAMPLE, 1000, 1000, force=True)
        self.assertEqual(scraper.calls, [number])
        self.assertEqual(job.skipped, 0)
        self.assertEqual(store.checks[number][0], "empty")

    def test_delay_antar_nomor_memakai_batas_yang_diberikan(self):
        delays = []
        collector = Collector(
            FakeStore(),
            FakeScraper(),
            sleep=delays.append,
            delay_min=2.0,
            delay_max=2.0,
        )
        collector.collect(SAMPLE, 1000, 1002)
        self.assertEqual(delays, [2.0, 2.0])

    def test_found_menyimpan_baris_dan_status(self):
        number = str(SAMPLE.with_sequence(1000))
        store = FakeStore()
        scraper = FakeScraper(
            {number: ScrapeResult(status="found", rows=[{"brand": "acer"}])}
        )
        Collector(store, scraper, sleep=lambda _: None).collect(SAMPLE, 1000, 1000)
        self.assertEqual(store.rows_written[number][0]["brand"], "acer")
        self.assertEqual(store.checks[number][0], "found")

    def test_empty_menghapus_baris(self):
        number = str(SAMPLE.with_sequence(1000))
        store = FakeStore()
        Collector(store, FakeScraper(), sleep=lambda _: None).collect(SAMPLE, 1000, 1000)
        self.assertIn(number, store.deleted)
        self.assertEqual(store.checks[number][0], "empty")

    def test_error_dicatat_dan_job_lanjut(self):
        fail = str(SAMPLE.with_sequence(1000))
        store = FakeStore()
        scraper = FakeScraper(fail_on={fail})
        job = Collector(store, scraper, sleep=lambda _: None).collect(SAMPLE, 1000, 1001)
        self.assertEqual(store.checks[fail][0], "error")
        self.assertEqual(job.status, "done")
        self.assertEqual(job.errors, 1)

    def test_cancel_menghentikan_loop(self):
        store = FakeStore()
        scraper = FakeScraper()
        collector = Collector(store, scraper, sleep=lambda _: None)
        collector.cancel()
        job = collector.collect(SAMPLE, 1000, 1005)
        self.assertEqual(scraper.calls, [])
        self.assertEqual(job.status, "cancelled")

    def test_sesi_kedaluwarsa_menghentikan_job_dan_tidak_retry(self):
        number = str(SAMPLE.with_sequence(1000))
        store = FakeStore()
        scraper = FakeScraper(error=AuthError("expired"))
        job = Collector(store, scraper, sleep=lambda _: None, max_retries=3).collect(
            SAMPLE, 1000, 1002
        )
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.errors, 1)
        self.assertEqual(job.last_error, "belum_login: expired")
        self.assertEqual(store.checks[number][0], "error")
        self.assertEqual(scraper.calls, [number])

    def test_progress_dihitung(self):
        store = FakeStore()
        job = Collector(store, FakeScraper(), sleep=lambda _: None).collect(SAMPLE, 1000, 1001)
        self.assertEqual(job.done, 2)
        self.assertEqual(job.progress, 1.0)

    def test_invariant_done_sama_dengan_hasil_plus_error(self):
        fail = str(SAMPLE.with_sequence(1001))
        store = FakeStore()
        scraper = FakeScraper(
            {str(SAMPLE.with_sequence(1000)): ScrapeResult(status="found", rows=[])},
            fail_on={fail},
        )
        job = Collector(store, scraper, sleep=lambda _: None).collect(SAMPLE, 1000, 1002)
        self.assertEqual(job.done, job.found + job.empty + job.errors)
        self.assertEqual(job.done, 3)

    def test_db_mati_menghentikan_job(self):
        store = FakeStore()
        scraper = FakeScraper(error=DbUnavailableError("down"))
        job = Collector(store, scraper, sleep=lambda _: None).collect(SAMPLE, 1000, 1002)
        self.assertEqual(job.status, "failed")
        self.assertIn("db_unavailable", job.last_error)
        self.assertEqual(scraper.calls, [str(SAMPLE.with_sequence(1000))])

    def test_job_state_awal(self):
        job = JobState(total=10)
        self.assertEqual(job.status, "idle")
        self.assertEqual(job.progress, 0.0)


if __name__ == "__main__":
    unittest.main()
