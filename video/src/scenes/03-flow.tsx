import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, Headline, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const STEPS = [
  {title: 'Wniosek', sub: 'PDF albo DOCX', color: COLORS.blue},
  {title: 'Archiwum', sub: 'podobne sprawy', color: COLORS.sky},
  {title: 'Wydziały', sub: 'kto odpowiada', color: COLORS.violet},
  {title: 'Projekt', sub: 'pismo z cytatami', color: COLORS.amber},
  {title: 'Anonimizacja', sub: 'dane usunięte', color: COLORS.green},
  {title: 'Wysyłka', sub: 'decyzja urzędnika', color: COLORS.blue},
];

const BOX_W = 250;
const BOX_H = 280;
const GAP = 40;
const START = -850;
const BOX_Y = 80;

export default makeScene2D('03-flow', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const boxes = STEPS.map(() => createRef<Rect>());
  const arrows = STEPS.map(() => createRef<Txt>());
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'JAK TO DZIAŁA'} x={-620} y={-400} />);
  view.add(
    <Headline
      ref={head}
      text={'Jedna ścieżka: od wgranego wniosku do wysłanej odpowiedzi'}
      x={-620}
      y={-290}
      size={56}
      width={1560}
    />,
  );

  STEPS.forEach((s, i) => {
    const cx = START + BOX_W / 2 + i * (BOX_W + GAP);
    view.add(
      <Rect
        ref={boxes[i]}
        x={cx}
        y={BOX_Y + 30}
        width={BOX_W}
        height={BOX_H}
        radius={18}
        fill={'#0C1524'}
        stroke={'#1E2C42'}
        lineWidth={1.5}
        layout={false}
        opacity={0}
      >
        <Rect width={214} height={5} radius={3} fill={s.color} y={-136} layout={false} />
        <Txt
          text={`0${i + 1}`}
          x={-95}
          y={-85}
          offsetX={-1}
          fill={s.color}
          fontFamily={FONT}
          fontSize={20}
          fontWeight={700}
          letterSpacing={2}
        />
        <Txt
          text={s.title}
          x={-95}
          y={-20}
          offsetX={-1}
          offsetY={-0.5}
          width={190}
          textWrap
          textAlign={'left'}
          fill={COLORS.text}
          fontFamily={FONT}
          fontSize={27}
          fontWeight={700}
          lineHeight={32}
        />
        <Txt
          text={s.sub}
          x={-95}
          y={75}
          offsetX={-1}
          offsetY={-0.5}
          width={190}
          textWrap
          textAlign={'left'}
          fill={COLORS.dim}
          fontFamily={FONT}
          fontSize={18}
          fontWeight={400}
          lineHeight={24}
        />
      </Rect>,
    );
    if (i < STEPS.length - 1) {
      view.add(
        <Txt
          ref={arrows[i]}
          text={'→'}
          x={cx + BOX_W / 2 + GAP / 2}
          y={BOX_Y}
          fill={COLORS.muted}
          fontFamily={FONT}
          fontSize={30}
          fontWeight={500}
          opacity={0}
        />,
      );
    }
  });

  view.add(
    <Txt
      ref={foot}
      text={'Każdy krok to osobny moduł — można go podmienić albo wyłączyć w ustawieniach.'}
      x={-620}
      y={360}
      offsetX={-1}
      offsetY={-0.5}
      width={1500}
      textWrap
      textAlign={'left'}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={24}
      fontWeight={400}
      lineHeight={34}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4), head().opacity(1, 0.6, easeOutCubic));
  for (let i = 0; i < STEPS.length; i++) {
    yield* all(boxes[i]().opacity(1, 0.35, easeOutCubic), boxes[i]().y(BOX_Y, 0.35, easeOutCubic));
    if (i < STEPS.length - 1) {
      yield* arrows[i]().opacity(1, 0.2);
    }
  }
  yield* foot().opacity(1, 0.6, easeOutCubic);
  yield* waitFor(10.0);
});
