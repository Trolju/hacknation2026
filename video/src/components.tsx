import {Circle, Gradient, Line, Rect, Txt, Video} from '@revideo/2d';
import type {Reference} from '@revideo/core';
import {CARD, CARD_SRC_H, COLORS, FONT} from './theme';

/** Tło: ciemny granat, dwie poświaty i siatka. */
export function Backdrop({grid = true}: {grid?: boolean}) {
  return (
    <Rect width={1920} height={1080} fill={COLORS.bg} layout={false}>
      <Circle
        width={1900}
        height={1900}
        x={-520}
        y={-620}
        fill={
          new Gradient({
            type: 'radial',
            from: [0, 0],
            to: [950, 0],
            stops: [
              {offset: 0, color: '#1D4ED866'},
              {offset: 0.5, color: '#1D4ED81A'},
              {offset: 1, color: '#05080F00'},
            ],
          })
        }
      />
      <Circle
        width={1500}
        height={1500}
        x={820}
        y={600}
        fill={
          new Gradient({
            type: 'radial',
            from: [0, 0],
            to: [750, 0],
            stops: [
              {offset: 0, color: '#0EA5E93D'},
              {offset: 1, color: '#05080F00'},
            ],
          })
        }
      />
      {grid &&
        Array.from({length: 13}, (_, i) => (
          <Line
            points={[
              [-960, -540 + i * 90],
              [960, -540 + i * 90],
            ]}
            stroke={'#1E2A3D'}
            lineWidth={1}
            opacity={0.22}
          />
        ))}
      {grid &&
        Array.from({length: 22}, (_, i) => (
          <Line
            points={[
              [-960 + i * 90, -540],
              [-960 + i * 90, 540],
            ]}
            stroke={'#1E2A3D'}
            lineWidth={1}
            opacity={0.22}
          />
        ))}
    </Rect>
  );
}

export function Kicker({
  text,
  x = -600,
  y = -470,
  color = COLORS.sky,
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  color?: string;
  ref?: Reference<Rect>;
}) {
  return (
    <Rect ref={ref} layout={false} x={x} y={y}>
      <Rect width={44} height={3} radius={2} fill={color} x={22} y={0} />
      <Txt
        text={text}
        x={60}
        y={0}
        offsetX={-1}
        fill={color}
        fontFamily={FONT}
        fontSize={19}
        fontWeight={600}
        letterSpacing={3.4}
      />
    </Rect>
  );
}

export function Headline({
  text,
  x = -600,
  y = -410,
  size = 48,
  width = 1200,
  color = COLORS.text,
  weight = 700,
  align = 'left',
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  size?: number;
  width?: number;
  color?: string;
  weight?: number;
  align?: 'left' | 'center' | 'right';
  ref?: Reference<Txt>;
}) {
  return (
    <Txt
      ref={ref}
      text={text}
      x={x}
      y={y}
      offsetX={align === 'left' ? -1 : align === 'right' ? 1 : 0}
      offsetY={-0.5}
      width={width}
      textWrap
      textAlign={align}
      fill={color}
      fontFamily={FONT}
      fontSize={size}
      fontWeight={weight}
      lineHeight={size * 1.14}
      letterSpacing={-0.6}
    />
  );
}

export function Subline({
  text,
  x = -600,
  y = -340,
  size = 24,
  width = 1180,
  color = COLORS.muted,
  align = 'left',
}: {
  text: string;
  x?: number;
  y?: number;
  size?: number;
  width?: number;
  color?: string;
  align?: 'left' | 'center' | 'right';
}) {
  return (
    <Txt
      text={text}
      x={x}
      y={y}
      offsetX={align === 'left' ? -1 : align === 'right' ? 1 : 0}
      offsetY={-0.5}
      width={width}
      textWrap
      textAlign={align}
      fill={color}
      fontFamily={FONT}
      fontSize={size}
      fontWeight={400}
      lineHeight={size * 1.45}
    />
  );
}

export const chipWidth = (text: string, size = 22) => Math.max(110, text.length * size * 0.58 + 46);

export function Chip({
  text,
  x = 0,
  y = 0,
  color = COLORS.blue,
  size = 22,
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  color?: string;
  size?: number;
  ref?: Reference<Rect>;
}) {
  const w = chipWidth(text, size);
  return (
    <Rect
      ref={ref}
      x={x}
      y={y}
      width={w}
      height={size + 32}
      radius={(size + 32) / 2}
      fill={'#0D1728'}
      stroke={color}
      lineWidth={1.5}
      layout={false}
      opacity={0}
    >
      <Txt
        text={text}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={size}
        fontWeight={500}
        letterSpacing={0.2}
      />
    </Rect>
  );
}

export function StatCard({
  value,
  label,
  accent,
  x,
  y = 40,
  w = 470,
  h = 300,
  ref,
}: {
  value: string;
  label: string;
  accent: string;
  x: number;
  y?: number;
  w?: number;
  h?: number;
  ref?: Reference<Rect>;
}) {
  return (
    <Rect
      ref={ref}
      x={x}
      y={y}
      width={w}
      height={h}
      radius={20}
      fill={'#0B1322'}
      stroke={'#1E2A3D'}
      lineWidth={1.5}
      layout={false}
      opacity={0}
    >
      <Rect width={w - 40} height={5} radius={3} fill={accent} y={-h / 2 + 20} layout={false} />
      <Txt
        text={value}
        x={-w / 2 + 30}
        y={-h / 2 + 78}
        offsetX={-1}
        offsetY={-0.5}
        fill={accent}
        fontFamily={FONT}
        fontSize={58}
        fontWeight={800}
        letterSpacing={-2}
      />
      <Txt
        text={label}
        x={-w / 2 + 30}
        y={h / 2 - 34}
        offsetX={-1}
        offsetY={1}
        width={w - 60}
        textWrap
        textAlign={'left'}
        fill={COLORS.muted}
        fontFamily={FONT}
        fontSize={21}
        fontWeight={400}
        lineHeight={30}
      />
    </Rect>
  );
}

/** Pasek postępu modułów pod kartą z nagraniem. */
export function ProgressRail({
  total,
  active,
  y = 508,
  accent = COLORS.blue,
}: {
  total: number;
  active: number;
  y?: number;
  accent?: string;
}) {
  const gap = 10;
  const w = 46;
  const start = -((total - 1) * (w + gap)) / 2;
  return (
    <Rect layout={false} y={y}>
      {Array.from({length: total}, (_, i) => (
        <Rect
          width={w}
          height={4}
          radius={2}
          x={start + i * (w + gap)}
          fill={i === active ? accent : i < active ? '#2A3A52' : '#182234'}
        />
      ))}
    </Rect>
  );
}

/**
 * Karta z nagraniem ekranu. `videoRef` steruje kamerą (scale/x/y),
 * więc punkt (fx, fy) ∈ [0,1]² źródła trafia w środek karty.
 */
export function FootageCard({
  src,
  rate = 1,
  cardRef,
  videoRef,
}: {
  src: string;
  rate?: number;
  cardRef?: Reference<Rect>;
  videoRef?: Reference<Video>;
}) {
  return (
    <Rect
      ref={cardRef}
      width={CARD.w}
      height={CARD.h}
      y={CARD.y}
      radius={CARD.radius}
      fill={COLORS.panel}
      stroke={'#26344A'}
      lineWidth={1.5}
      clip
      layout={false}
      opacity={0}
    >
      <Video
        ref={videoRef}
        src={src}
        width={CARD.w}
        height={CARD_SRC_H}
        play={true}
        playbackRate={rate}
      />
    </Rect>
  );
}

/** Przelicza punkt zainteresowania źródła na pozycję kamery. */
export function camPos(fx: number, fy: number, z: number) {
  return {
    x: -(fx - 0.5) * CARD.w * z,
    y: -(fy - 0.5) * CARD_SRC_H * z,
  };
}

/** Ciemna nakładka pod podpisy — czytelność na jasnym interfejsie. */
export function CardScrim() {
  return (
    <Rect
      width={CARD.w}
      height={270}
      y={CARD.y + CARD.h / 2 - 135}
      layout={false}
      fill={
        new Gradient({
          type: 'linear',
          from: [0, -135],
          to: [0, 135],
          stops: [
            {offset: 0, color: '#05080F00'},
            {offset: 0.22, color: '#05080F2E'},
            {offset: 0.5, color: '#05080F9E'},
            {offset: 0.78, color: '#05080FE0'},
            {offset: 1, color: '#05080FF5'},
          ],
        })
      }
    />
  );
}

/** Miękkie wygaszenie krawędzi karty — kadr zamiast uciętego interfejsu. */
export function CardVignette() {
  const w = 240;
  const stops = [
    {offset: 0, color: '#05080FB8'},
    {offset: 0.45, color: '#05080F52'},
    {offset: 1, color: '#05080F00'},
  ];
  return (
    <Rect width={CARD.w} height={CARD.h} y={CARD.y} layout={false}>
      <Rect
        width={w}
        height={CARD.h}
        x={-CARD.w / 2 + w / 2}
        layout={false}
        fill={new Gradient({type: 'linear', from: [-w / 2, 0], to: [w / 2, 0], stops})}
      />
      <Rect
        width={w}
        height={CARD.h}
        x={CARD.w / 2 - w / 2}
        layout={false}
        fill={new Gradient({type: 'linear', from: [w / 2, 0], to: [-w / 2, 0], stops})}
      />
    </Rect>
  );
}

/** Podpis modułu w lewym dolnym rogu karty. */
export function ModuleCaption({
  index,
  name,
  benefit,
  accent,
  ref,
}: {
  index: string;
  name: string;
  benefit: string;
  accent: string;
  ref?: Reference<Rect>;
}) {
  const left = -CARD.w / 2 + 56;
  const base = CARD.y + CARD.h / 2 - 46;
  return (
    <Rect ref={ref} layout={false} opacity={0}>
      <Rect width={5} height={104} radius={3} fill={accent} x={left - 22} y={base - 62} />
      <Txt
        text={index}
        x={left}
        y={base - 104}
        offsetX={-1}
        offsetY={-0.5}
        fill={accent}
        fontFamily={FONT}
        fontSize={22}
        fontWeight={700}
        letterSpacing={3}
      />
      <Txt
        text={name}
        x={left}
        y={base - 62}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={46}
        fontWeight={700}
        letterSpacing={-0.9}
      />
      <Txt
        text={benefit}
        x={left}
        y={base - 14}
        offsetX={-1}
        offsetY={-0.5}
        fill={'#C3D0E2'}
        fontFamily={FONT}
        fontSize={25}
        fontWeight={400}
      />
    </Rect>
  );
}

/** Chip z wynikiem, wysuwany w prawym dolnym rogu karty. */
export function ResultChip({
  text,
  accent,
  ref,
}: {
  text: string;
  accent: string;
  ref?: Reference<Rect>;
}) {
  const w = chipWidth(text, 26) + 24;
  return (
    <Rect
      ref={ref}
      x={CARD.w / 2 - 56 - w / 2}
      y={CARD.y + CARD.h / 2 - 62}
      width={w}
      height={62}
      radius={31}
      fill={'#05080FEE'}
      stroke={accent}
      lineWidth={2}
      layout={false}
      opacity={0}
      scale={0.85}
    >
      <Txt
        text={text}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={26}
        fontWeight={600}
        letterSpacing={0.2}
      />
    </Rect>
  );
}

/** Cienka smuga koloru przelatująca przez kadr — akcent przejścia. */
export function Sweep({color = COLORS.blue, ref}: {color?: string; ref?: Reference<Rect>}) {
  return (
    <Rect
      ref={ref}
      width={3}
      height={1080}
      fill={color}
      x={-1100}
      layout={false}
      opacity={0.9}
      shadowColor={color}
      shadowBlur={40}
    />
  );
}
