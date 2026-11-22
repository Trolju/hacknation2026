import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, delay, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const LEFT = -840;

const STEPS = [
  {
    n: '01',
    t: 'Wniosek wpływa',
    d: 'Kalendarz pilnuje terminu ustawowego i podświetla „dziś / jutro”.',
    c: COLORS.blue,
  },
  {
    n: '02',
    t: 'Dokumenty wgrane',
    d: 'PDF i Word trafiają do bazy wiedzy, pocięte na fragmenty.',
    c: COLORS.violet,
  },
  {
    n: '03',
    t: 'Kwerenda archiwum',
    d: 'Opis sprawy zamiast słów kluczowych — podobne sprawy i fragmenty.',
    c: COLORS.green,
  },
  {
    n: '04',
    t: 'Routing',
    d: 'Wskazanie wydziału z uzasadnieniem i poziomem pewności.',
    c: COLORS.amber,
  },
  {
    n: '05',
    t: 'Projekt pisma',
    d: 'Podstawa prawna i przypisy do źródeł. Decyzję podejmuje urzędnik.',
    c: COLORS.sky,
  },
];

const CARD_W = 320;
const CARD_H = 306;
const GAP = 20;
const TOTAL = STEPS.length * CARD_W + (STEPS.length - 1) * GAP;
const START = -TOTAL / 2 + CARD_W / 2;
const CARD_Y = 70;

export default makeScene2D('05-workflow', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const rail = createRef<Rect>();
  const cards = STEPS.map(() => createRef<Rect>());
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'JAK TO DZIAŁA'} x={LEFT - 40} y={-400} />);
  view.add(
    <Txt
      ref={head}
      text={'Pięć kroków. Zero pisania od zera.'}
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

  view.add(
    <Rect
      ref={rail}
      width={0}
      height={2}
      fill={'#1E2C3E'}
      x={-TOTAL / 2 + CARD_W / 2}
      y={CARD_Y - CARD_H / 2 - 40}
      offsetX={-1}
    />,
  );

  STEPS.forEach((s, i) => {
    const x = START + i * (CARD_W + GAP);
    view.add(
      <Rect
        ref={cards[i]}
        x={x}
        y={CARD_Y + 34}
        width={CARD_W}
        height={CARD_H}
        radius={18}
        fill={'#0B1320'}
        stroke={'#1E2C3E'}
        lineWidth={1.5}
        opacity={0}
        layout={false}
      >
        <Rect width={CARD_W - 36} height={4} radius={2} fill={s.c} y={-CARD_H / 2 + 3} />
        <Txt
          text={s.n}
          x={-CARD_W / 2 + 28}
          y={-CARD_H / 2 + 54}
          offsetX={-1}
          offsetY={-0.5}
          fill={s.c}
          fontFamily={FONT}
          fontSize={20}
          fontWeight={700}
          letterSpacing={2.4}
        />
        <Txt
          text={s.t}
          x={-CARD_W / 2 + 28}
          y={-CARD_H / 2 + 108}
          offsetX={-1}
          offsetY={-0.5}
          width={CARD_W - 56}
          textWrap
          textAlign={'left'}
          fill={COLORS.text}
          fontFamily={FONT}
          fontSize={27}
          fontWeight={700}
          lineHeight={33}
          letterSpacing={-0.5}
        />
        <Txt
          text={s.d}
          x={-CARD_W / 2 + 28}
          y={-CARD_H / 2 + 158}
          offsetX={-1}
          offsetY={-0.5}
          width={CARD_W - 56}
          textWrap
          textAlign={'left'}
          fill={'#93A4BC'}
          fontFamily={FONT}
          fontSize={19}
          fontWeight={400}
          lineHeight={27}
        />
      </Rect>,
    );
  });

  view.add(
    <Txt
      ref={foot}
      text={'Każdy krok zostawia ślad: kto, kiedy i co zmienił.'}
      x={LEFT}
      y={440}
      offsetX={-1}
      offsetY={-0.5}
      fill={'#6E8099'}
      fontFamily={FONT}
      fontSize={22}
      fontWeight={400}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(head().opacity(1, 0.5, easeOutCubic), head().y(-322, 0.5, easeOutCubic));
  yield* all(rail().width(TOTAL - CARD_W, 0.7, easeOutCubic), delay(0.1, cards[0]().opacity(1, 0.3)));

  yield* all(
    ...cards.map((c, i) =>
      delay(
        i * 0.1,
        all(c().opacity(1, 0.34, easeOutCubic), c().y(CARD_Y, 0.42, easeOutExpo)),
      ),
    ),
  );

  yield* all(foot().opacity(1, 0.5, easeOutCubic), foot().y(432, 0.5, easeOutCubic));
  yield* waitFor(3.2);
});
