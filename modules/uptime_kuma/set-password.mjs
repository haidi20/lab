// Set password admin Uptime Kuma lewat better-auth (hash sesuai skema server).
// Pakai: node set-password.mjs <username> <password>
import { hashPassword } from "better-auth/crypto";
import Database from "better-sqlite3";
import path from "node:path";

const [, , username = "admin", password = "admin"] = process.argv;
const dbPath = path.join(process.cwd(), "data", "kuma.db");

const hash = await hashPassword(password);
const db = new Database(dbPath);

const user = db.prepare("select id, username from better_auth_user where username = ?").get(username);
if (!user) {
    console.error(`user tidak ditemukan: ${username}`);
    process.exit(1);
}

const info = db
    .prepare("update better_auth_account set password = ? where accountId = ? and providerId = 'credential'")
    .run(hash, user.id);

console.log(`password ${username} diupdate (rows=${info.changes})`);
db.close();
