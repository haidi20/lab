import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Logo} from './template/Logo';
import {Title} from './template/Title';
import type {CoverProps} from './types';

export const KaltimCover: React.FC<CoverProps> = ({title, articles}) => (
  <AbsoluteFill style={{backgroundColor: '#0B1323', fontFamily: 'Poppins, Inter, Segoe UI, Arial, sans-serif'}}>
    <Logo
      logoColor1='#A3E635'
      logoColor2='#F59E0B'
      style={{top: '16%'}}
    />
    <Title
      titleText={title}
      titleColor='#F5FAFF'
      style={{fontSize: 72, bottom: 220, fontFamily: 'Poppins, Inter, Segoe UI, Arial, sans-serif'}}
    />
    {articles.map((article, index) => (
      <Title
        key={article.index}
        titleText={article.title}
        titleColor='#C7D2FE'
        from={30 + index * 12}
        style={{fontSize: 34, bottom: 540 - index * 110, fontWeight: 600, fontFamily: 'Poppins, Inter, Segoe UI, Arial, sans-serif'}}
      />
    ))}
  </AbsoluteFill>
);
