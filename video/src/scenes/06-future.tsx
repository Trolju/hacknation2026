import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, Headline, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const COLS = [
  {
    tag: 'DZIŚ',
    title: 'Bydgoszcz, Wydział Organizacji i Kadr',
    body: 'Prototyp na prawdziwych wnioskach. Tryb demo i tryb realny, przełączane w ustawieniach.',
    color: COLORS.blue,
  },
  {
    tag: 'JUTRO',
    title: 'Jedna instancja w urzędzie',
    body: 'Serwer w serwerowni miasta. Dokumenty nie wychodzą poza sieć urzędu.',
    color: COLORS.sky,
  },
  {
    tag: 'ZA ROK',
    title: 'Archiwum, które rośnie',
    body: 'Każda zamknięta sprawa uczy wyszukiwanie. Nowe komórki dochodzą bez wdrożenia.',
    color: COLORS.violet,
  },
];

const COL_W = 460;
const COL_GAP = 40;
const COL_START = -730;

export default makeScene2D('06-future', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const cols = COLS.map(() => createRef<Rect>());
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'DLA KOGO'} x={-620} y={-430} />);
  view.add(
    <Headline
      ref={head}
      text={'Dla urzędników, którzy obsługują wnioski UDIP'}
      x={-620}
      y={-330}
      size={56}
      width={1560}
    />,
  );

  COLS.forEach((c, i) => {
    const cx = COL_START + COL_W / 2 + i * (COL_W + COL_GAP);
    view.add(
      <Rect
        ref={cols[i]}
        x={cx}
        y={90}
        width={COL_W}
        height={310}
        radius={18}
        fill={'#0C1524'}
        stroke={'#1E2C42'}
        lineWidth={1.5}
        layout={false}
        opacity={0}
      >
        <Rect width={424} height={5} radius={3} fill={c.color} y={-148} layout={false} />
        <Txt
          text={c.tag}
          x={-195}
          y={-100}
          offsetX={-1}
          fill={c.color}
          fontFamily={FONT}
          fontSize={17}
          fontWeight={700}
          letterSpacing={2.6}
        />
        <Txt
          text={c.title}
          x={-195}
          y={-30}
          offsetX={-1}
          offsetY={-0.5}
          width={390}
          textWrap
          textAlign={'left'}
          fill={COLORS.text}
          fontFamily={FONT}
          fontSize={27}
          fontWeight={700}
          lineHeight={34}
        />
        <Txt
          text={c.body}
          x={-195}
          y={80}
          offsetX={-1}
          offsetY={-0.5}
          width={390}
          textWrap
          textAlign={'left'}
          fill={COLORS.muted}
          fontFamily={FONT}
          fontSize={20}
          fontWeight={400}
          lineHeight={30}
        />
      </Rect>,
    );
  });

  view.add(
    <Txt
      ref={foot}
      text={'Nie zastępuje urzędnika. Zdejmuje z niego przepisywanie.'}
      x={-620}
      y={340}
      offsetX={-1}
      offsetY={-0.5}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={26}
      fontWeight={500}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4), head().opacity(1, 0.6, easeOutCubic));
  for (const c of cols) {
    yield* all(c().opacity(1, 0.45, easeOutCubic), c().y(60, 0.45, easeOutCubic));
  }
  yield* foot().opacity(1, 0.6, easeOutCubic);
  yield* waitFor(9.0);
});
