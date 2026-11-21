import {Circle, Gradient, Img, Line, Rect, Txt} from '@revideo/2d';
import type {Reference} from '@revideo/core';
import {COLORS, FONT} from './theme';

/** Tło: ciemny granat, poświata i siatka. */
export function Backdrop() {
  return (
    <Rect width={1920} height={1080} fill={COLORS.bg} layout={false}>
      <Circle
        width={1700}
        height={1700}
        x={-420}
        y={-520}
        fill={
          new Gradient({
            type: 'radial',
            from: [0, 0],
            to: [850, 0],
            stops: [
              {offset: 0, color: '#1D4ED855'},
              {offset: 0.55, color: '#1D4ED818'},
              {offset: 1, color: '#060A1300'},
            ],
          })
        }
      />
      <Circle
        width={1300}
        height={1300}
        x={760}
        y={520}
        fill={
          new Gradient({
            type: 'radial',
            from: [0, 0],
            to: [650, 0],
            stops: [
              {offset: 0, color: '#0EA5E933'},
              {offset: 1, color: '#060A1300'},
            ],
          })
        }
      />
      {Array.from({length: 13}, (_, i) => (
        <Line
          points={[
            [-960, -540 + i * 90],
            [960, -540 + i * 90],
          ]}
          stroke={'#1E293B'}
          lineWidth={1}
          opacity={0.28}
        />
      ))}
      {Array.from({length: 22}, (_, i) => (
        <Line
          points={[
            [-960 + i * 90, -540],
            [-960 + i * 90, 540],
          ]}
          stroke={'#1E293B'}
          lineWidth={1}
          opacity={0.28}
        />
      ))}
    </Rect>
  );
}

export function Kicker({
  text,
  x = -600,
  y = -470,
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  ref?: Reference<Rect>;
}) {
  return (
    <Rect ref={ref} layout={false} x={x} y={y}>
      <Rect width={44} height={3} radius={2} fill={COLORS.blue} x={22} y={0} />
      <Txt
        text={text}
        x={44 + 16}
        y={0}
        offsetX={-1}
        fill={COLORS.sky}
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
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  size?: number;
  width?: number;
  color?: string;
  ref?: Reference<Txt>;
}) {
  return (
    <Txt
      ref={ref}
      text={text}
      x={x}
      y={y}
      offsetX={-1}
      offsetY={-0.5}
      width={width}
      textWrap
      textAlign={'left'}
      fill={color}
      fontFamily={FONT}
      fontSize={size}
      fontWeight={700}
      lineHeight={size * 1.16}
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
}: {
  text: string;
  x?: number;
  y?: number;
  size?: number;
  width?: number;
  color?: string;
}) {
  return (
    <Txt
      text={text}
      x={x}
      y={y}
      offsetX={-1}
      offsetY={-0.5}
      width={width}
      textWrap
      textAlign={'left'}
      fill={color}
      fontFamily={FONT}
      fontSize={size}
      fontWeight={400}
      lineHeight={size * 1.45}
    />
  );
}

/** Zrzut ekranu w ramce przeglądarki. */
export function BrowserCard({
  src,
  url,
  width = 1200,
  y = 0,
  ref,
  imageRef,
}: {
  src: string;
  url: string;
  width?: number;
  y?: number;
  ref?: Reference<Rect>;
  imageRef?: Reference<Img>;
}) {
  const barH = 42;
  const imgH = width / 1.6;
  const totalH = imgH + barH;
  const top = -totalH / 2;

  return (
    <Rect
      ref={ref}
      width={width}
      height={totalH}
      y={y}
      radius={18}
      fill={COLORS.panel}
      stroke={'#243449'}
      lineWidth={1.5}
      clip
      layout={false}
    >
      <Rect width={width} height={barH} fill={'#0A1120'} y={top + barH / 2} layout={false} />
      <Circle width={11} height={11} fill={'#EF4444'} x={-width / 2 + 26} y={top + barH / 2} />
      <Circle width={11} height={11} fill={'#F59E0B'} x={-width / 2 + 46} y={top + barH / 2} />
      <Circle width={11} height={11} fill={'#10B981'} x={-width / 2 + 66} y={top + barH / 2} />
      <Rect
        width={520}
        height={24}
        radius={7}
        fill={'#111C2E'}
        x={0}
        y={top + barH / 2}
        layout={false}
      >
        <Txt
          text={url}
          fill={COLORS.dim}
          fontFamily={FONT}
          fontSize={14}
          fontWeight={500}
          letterSpacing={0.2}
        />
      </Rect>
      <Img ref={imageRef} src={src} width={width} height={imgH} y={barH / 2} />
    </Rect>
  );
}

export const chipWidth = (text: string) => Math.max(120, text.length * 13.2 + 44);

export function Chip({
  text,
  x = 0,
  y = 0,
  color = COLORS.blue,
  ref,
}: {
  text: string;
  x?: number;
  y?: number;
  color?: string;
  ref?: Reference<Rect>;
}) {
  const w = chipWidth(text);
  return (
    <Rect
      ref={ref}
      x={x}
      y={y}
      width={w}
      height={54}
      radius={27}
      fill={'#0F1B2E'}
      stroke={color}
      lineWidth={1.5}
      layout={false}
      opacity={0}
    >
      <Txt
        text={text}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={22}
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
  ref,
}: {
  value: string;
  label: string;
  accent: string;
  x: number;
  y?: number;
  ref?: Reference<Rect>;
}) {
  return (
    <Rect
      ref={ref}
      x={x}
      y={y}
      width={470}
      height={300}
      radius={20}
      fill={'#0C1524'}
      stroke={'#1E2C42'}
      lineWidth={1.5}
      layout={false}
    >
      <Rect width={430} height={5} radius={3} fill={accent} y={-140} layout={false} />
      <Txt
        text={value}
        x={-195}
        y={-58}
        offsetX={-1}
        fill={accent}
        fontFamily={FONT}
        fontSize={64}
        fontWeight={800}
        letterSpacing={-2}
      />
      <Txt
        text={label}
        x={-195}
        y={62}
        offsetX={-1}
        offsetY={-0.5}
        width={390}
        textWrap
        textAlign={'left'}
        fill={COLORS.muted}
        fontFamily={FONT}
        fontSize={22}
        fontWeight={400}
        lineHeight={32}
      />
    </Rect>
  );
}

export function ProgressDots({
  total,
  active,
  y = 512,
}: {
  total: number;
  active: number;
  y?: number;
}) {
  const gap = 26;
  const start = -((total - 1) * gap) / 2;
  return (
    <Rect layout={false} y={y}>
      {Array.from({length: total}, (_, i) => (
        <Circle
          width={i === active ? 26 : 9}
          height={9}
          radius={5}
          x={start + i * gap}
          fill={i === active ? COLORS.blue : '#243449'}
        />
      ))}
    </Rect>
  );
}
