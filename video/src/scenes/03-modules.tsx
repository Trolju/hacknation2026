import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, delay, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop} from '../components';
import {FEATURES} from '../features';
import {COLORS, FONT} from '../theme';

const TILE_W = 440;
const TILE_H = 132;
const GAP = 24;

export default makeScene2D('03-modules', function* (view) {
  const head = createRef<Txt>();
  const tiles = FEATURES.map(() => createRef<Rect>());
  const tail = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(
    <Txt
      ref={head}
      text={'Osiem modułów.'}
      x={0}
      y={-300}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={104}
      fontWeight={800}
      letterSpacing={-3}
      opacity={0}
      scale={1.08}
    />,
  );

  const totalW = 4 * TILE_W + 3 * GAP;
  view.add(
    <Rect layout={false}>
      {FEATURES.map((f, i) => {
        const col = i % 4;
        const row = Math.floor(i / 4);
        const x = -totalW / 2 + TILE_W / 2 + col * (TILE_W + GAP);
        const y = -20 + row * (TILE_H + GAP);
        return (
          <Rect
            ref={tiles[i]}
            key={f.id}
            x={x}
            y={y + 44}
            width={TILE_W}
            height={TILE_H}
            radius={14}
            fill={'#0B1322'}
            stroke={'#1E2A3D'}
            lineWidth={1.5}
            layout={false}
            opacity={0}
          >
            <Rect width={4} height={TILE_H - 40} radius={2} fill={f.accent} x={-TILE_W / 2 + 22} />
            <Txt
              text={f.index}
              x={-TILE_W / 2 + 44}
              y={-20}
              offsetX={-1}
              offsetY={-0.5}
              fill={f.accent}
              fontFamily={FONT}
              fontSize={17}
              fontWeight={700}
              letterSpacing={2.4}
            />
            <Txt
              text={f.name}
              x={-TILE_W / 2 + 44}
              y={16}
              offsetX={-1}
              offsetY={-0.5}
              fill={COLORS.text}
              fontFamily={FONT}
              fontSize={27}
              fontWeight={600}
              letterSpacing={-0.4}
            />
          </Rect>
        );
      })}
    </Rect>,
  );

  view.add(
    <Txt
      ref={tail}
      text={'Jeden dzień pracy.'}
      x={0}
      y={360}
      fill={COLORS.sky}
      fontFamily={FONT}
      fontSize={54}
      fontWeight={700}
      letterSpacing={-1.2}
      opacity={0}
    />,
  );

  yield* all(head().opacity(1, 0.4, easeOutExpo), head().scale(1, 0.5, easeOutExpo));

  yield* all(
    ...tiles.map((t, i) =>
      delay(
        i * 0.075,
        all(t().opacity(1, 0.3, easeOutCubic), t().y(t().y() - 44, 0.36, easeOutCubic)),
      ),
    ),
  );

  yield* waitFor(0.35);
  yield* all(tail().opacity(1, 0.4, easeOutCubic), tail().y(348, 0.4, easeOutCubic));
  yield* waitFor(0.85);
});
