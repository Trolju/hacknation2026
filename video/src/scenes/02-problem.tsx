import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, Headline, Kicker, StatCard} from '../components';
import {COLORS, FONT} from '../theme';

const STATS = [
  {
    value: 'dziesiątki',
    label: 'wniosków w jednej kolejce, każdy z własnym terminem ustawowym',
    accent: COLORS.blue,
  },
  {
    value: '14 dni',
    label: 'na odpowiedź — termin, którego nikt nie pilnuje poza urzędnikiem',
    accent: COLORS.amber,
  },
  {
    value: 'setki godzin',
    label: 'rocznie na przepisywanie tego, co urząd już raz napisał',
    accent: COLORS.violet,
  },
];

export default makeScene2D('02-problem', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const cards = STATS.map(() => createRef<Rect>());
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'PROBLEM'} x={-620} y={-430} />);
  view.add(
    <Headline
      ref={head}
      text={'14 dni. Setki godzin. Zero miejsca na błąd.'}
      x={-620}
      y={-300}
      size={64}
      width={1500}
    />,
  );

  STATS.forEach((s, i) => {
    view.add(
      <StatCard
        ref={cards[i]}
        value={s.value}
        label={s.label}
        accent={s.accent}
        x={-620 + 470 / 2 + i * 500}
        y={36}
      />,
    );
  });

  view.add(
    <Txt
      ref={foot}
      text={
        'A w każdym z tych dokumentów są dane osobowe, których nie wolno wysłać byle gdzie.'
      }
      x={-620}
      y={300}
      offsetX={-1}
      offsetY={-0.5}
      width={1500}
      textWrap
      textAlign={'left'}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={26}
      fontWeight={400}
      lineHeight={38}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4), head().opacity(1, 0.6, easeOutCubic));
  for (const c of cards) {
    yield* all(c().opacity(1, 0.45, easeOutCubic), c().y(0, 0.45, easeOutCubic));
  }
  yield* foot().opacity(1, 0.6, easeOutCubic);
  yield* waitFor(13.0);
});
