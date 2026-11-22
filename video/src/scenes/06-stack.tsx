import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, delay, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const LEFT = -840;

const GROUPS = [
  {
    label: 'BACKEND',
    color: COLORS.blue,
    items: ['Python 3.12', 'FastAPI', 'Pydantic v2', 'SQLite', 'pytest'],
  },
  {
    label: 'FRONTEND',
    color: COLORS.sky,
    items: ['React 18', 'TypeScript', 'TanStack Query', 'Vite', 'vitest'],
  },
  {
    label: 'AI',
    color: COLORS.violet,
    items: ['llama.cpp', 'Bielik 11B', 'Ollama', 'embeddings'],
  },
  {
    label: 'WDROŻENIE',
    color: COLORS.teal,
    items: ['Docker', 'docker compose', 'nginx', 'Makefile'],
  },
];

const COL_W = 410;
const GAP = 24;

export default makeScene2D('06-stack', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const cols = GROUPS.map(() => createRef<Rect>());
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'NARZĘDZIA'} x={LEFT - 40} y={-400} color={COLORS.violet} />);
  view.add(
    <Txt
      ref={head}
      text={'Otwarty stos. Bez licencji na start.'}
      x={LEFT}
      y={-330}
      offsetX={-1}
      offsetY={-0.5}
      width={1500}
      textWrap
      textAlign={'left'}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={66}
      fontWeight={700}
      lineHeight={78}
      letterSpacing={-1.4}
      opacity={0}
    />,
  );

  const totalW = GROUPS.length * COL_W + (GROUPS.length - 1) * GAP;
  view.add(
    <Rect layout={false}>
      {GROUPS.map((g, i) => {
        const x = -totalW / 2 + COL_W / 2 + i * (COL_W + GAP);
        return (
          <Rect ref={cols[i]} key={g.label} x={x} y={60} width={COL_W} layout={false} opacity={0}>
            <Rect width={COL_W} height={2} fill={g.color} y={-158} opacity={0.85} />
            <Txt
              text={g.label}
              x={-COL_W / 2}
              y={-124}
              offsetX={-1}
              offsetY={-0.5}
              fill={g.color}
              fontFamily={FONT}
              fontSize={19}
              fontWeight={700}
              letterSpacing={3.2}
            />
            {g.items.map((it, j) => (
              <Rect
                key={it}
                x={0}
                y={-58 + j * 70}
                width={COL_W}
                height={58}
                radius={12}
                fill={'#0B1322'}
                stroke={'#1E2A3D'}
                lineWidth={1.2}
                layout={false}
              >
                <Txt
                  text={it}
                  x={-COL_W / 2 + 20}
                  offsetX={-1}
                  offsetY={-0.5}
                  fill={COLORS.text}
                  fontFamily={FONT}
                  fontSize={24}
                  fontWeight={500}
                />
              </Rect>
            ))}
          </Rect>
        );
      })}
    </Rect>,
  );

  view.add(
    <Txt
      ref={foot}
      text={'Wszystko open source. Całość wstaje jedną komendą: docker compose up.'}
      x={0}
      y={440}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={24}
      fontWeight={500}
      letterSpacing={0.3}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(head().opacity(1, 0.5, easeOutCubic), head().y(-322, 0.5, easeOutCubic));

  yield* all(
    ...GROUPS.map((_, i) =>
      delay(
        i * 0.16,
        all(cols[i]().opacity(1, 0.4, easeOutCubic), cols[i]().y(44, 0.5, easeOutExpo)),
      ),
    ),
  );

  yield* all(foot().opacity(1, 0.5, easeOutCubic), foot().y(432, 0.5, easeOutCubic));
  yield* waitFor(3.4);
});
