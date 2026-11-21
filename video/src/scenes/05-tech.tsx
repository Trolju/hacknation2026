import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import type {Reference} from '@revideo/core';
import {Backdrop, Chip, Headline, Kicker, chipWidth} from '../components';
import {COLORS, FONT} from '../theme';

const ROWS = [
  {
    label: 'BACKEND',
    items: ['Python 3.12', 'FastAPI', 'Pydantic v2', 'SQLite', 'pytest'],
    y: -120,
  },
  {
    label: 'FRONTEND',
    items: ['React 18', 'TypeScript', 'TanStack Query', 'Vite', 'vitest'],
    y: -10,
  },
  {
    label: 'LOKALNE AI',
    items: ['llama.cpp', 'Bielik 11B v2.3', 'Ollama'],
    y: 100,
  },
  {
    label: 'WDROŻENIE',
    items: ['Docker', 'docker compose', 'nginx', 'Makefile'],
    y: 210,
  },
];

const CHIP_START = -330;
const CHIP_GAP = 18;

export default makeScene2D('05-tech', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const labels = ROWS.map(() => createRef<Txt>());
  const chips: Reference<Rect>[][] = ROWS.map((r) => r.items.map(() => createRef<Rect>()));
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'NARZĘDZIA'} x={-620} y={-400} />);
  view.add(
    <Headline
      ref={head}
      text={'Stos, który da się utrzymać w urzędzie'}
      x={-620}
      y={-300}
      size={56}
      width={1560}
    />,
  );

  ROWS.forEach((row, ri) => {
    view.add(
      <Txt
        ref={labels[ri]}
        text={row.label}
        x={-620}
        y={row.y}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.dim}
        fontFamily={FONT}
        fontSize={17}
        fontWeight={600}
        letterSpacing={2.6}
        opacity={0}
      />,
    );
    let x = CHIP_START;
    row.items.forEach((item, ci) => {
      const w = chipWidth(item);
      view.add(<Chip ref={chips[ri][ci]} text={item} x={x + w / 2} y={row.y} />);
      x += w + CHIP_GAP;
    });
  });

  view.add(
    <Txt
      ref={foot}
      text={
        'Porty i adaptery — domena nie zna HTTP-a  ·  tryb atrapy działa bez modelu i bez sieci  ·  make check przed commitem'
      }
      x={-620}
      y={320}
      offsetX={-1}
      offsetY={-0.5}
      width={1560}
      textWrap
      textAlign={'left'}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={23}
      fontWeight={400}
      lineHeight={34}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4), head().opacity(1, 0.6, easeOutCubic));
  for (let ri = 0; ri < ROWS.length; ri++) {
    yield* labels[ri]().opacity(1, 0.3);
    for (let ci = 0; ci < ROWS[ri].items.length; ci++) {
      yield* chips[ri][ci]().opacity(1, 0.22, easeOutCubic);
    }
  }
  yield* foot().opacity(1, 0.6, easeOutCubic);
  yield* waitFor(11.0);
});
