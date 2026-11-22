import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const LEFT = -840;

const PAINS = [
  {num: 'dziesiątki', label: 'wniosków o udostępnienie informacji publicznej — każdego dnia', color: COLORS.amber},
  {num: 'setki godzin', label: 'na ręcznym przeszukiwaniu archiwów i weryfikacji stron BIP', color: COLORS.amber},
  {num: 'te same pisma', label: 'pisane od nowa, bo wiedza z poprzednich spraw nie jest pod ręką', color: COLORS.red},
];

export default makeScene2D('02-problem', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const rows = PAINS.map(() => createRef<Rect>());
  const painGroup = createRef<Rect>();

  const oldLabel = createRef<Txt>();
  const strike = createRef<Rect>();
  const arrow = createRef<Rect>();
  const newLabel = createRef<Txt>();
  const newSub = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'PROBLEM'} x={LEFT - 40} y={-400} color={COLORS.amber} />);
  view.add(
    <Txt
      ref={head}
      text={'Jedno pismo. Kilka dni pracy urzędnika.'}
      x={LEFT}
      y={-330}
      offsetX={-1}
      offsetY={-0.5}
      width={1500}
      textWrap
      textAlign={'left'}
      fill={COLORS.text}
      fontFamily={FONT}
      fontSize={72}
      fontWeight={700}
      lineHeight={84}
      letterSpacing={-1.6}
      opacity={0}
    />,
  );

  view.add(
    <Rect ref={painGroup} layout={false}>
      {PAINS.map((p, i) => (
        <Rect ref={rows[i]} key={i} layout={false} y={-40 + i * 190} opacity={0}>
          <Rect width={4} height={124} radius={2} fill={p.color} x={LEFT - 26} y={0} />
          <Txt
            text={p.num}
            x={LEFT}
            y={-22}
            offsetX={-1}
            offsetY={-0.5}
            fill={p.color}
            fontFamily={FONT}
            fontSize={64}
            fontWeight={800}
            letterSpacing={-1.6}
          />
          <Txt
            text={p.label}
            x={LEFT}
            y={38}
            offsetX={-1}
            offsetY={-0.5}
            width={1420}
            textWrap
            textAlign={'left'}
            fill={COLORS.muted}
            fontFamily={FONT}
            fontSize={28}
            fontWeight={400}
            lineHeight={38}
          />
        </Rect>
      ))}
    </Rect>,
  );

  view.add(
    <Txt
      ref={oldLabel}
      text={'kilka dni'}
      x={0}
      y={-150}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={96}
      fontWeight={800}
      letterSpacing={-3}
      opacity={0}
    />,
  );
  view.add(<Rect ref={strike} width={0} height={7} radius={4} fill={COLORS.red} x={0} y={-150} />);
  view.add(
    <Rect ref={arrow} layout={false} y={-30} opacity={0}>
      <Rect width={3} height={54} fill={COLORS.blue} x={0} y={0} />
      <Rect width={18} height={18} radius={9} fill={COLORS.blue} x={0} y={-30} />
    </Rect>,
  );
  view.add(
    <Txt
      ref={newLabel}
      text={'kilka minut'}
      x={0}
      y={110}
      fill={COLORS.green}
      fontFamily={FONT}
      fontSize={148}
      fontWeight={800}
      letterSpacing={-5}
      opacity={0}
      scale={1.12}
    />,
  );
  view.add(
    <Txt
      ref={newSub}
      text={'Tyle ma trwać przygotowanie odpowiedzi na wniosek UDIP.'}
      x={0}
      y={232}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={30}
      fontWeight={400}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(head().opacity(1, 0.5, easeOutCubic), head().y(-322, 0.5, easeOutCubic));

  for (let i = 0; i < rows.length; i++) {
    yield* all(rows[i]().opacity(1, 0.34, easeOutCubic), rows[i]().x(24, 0.42, easeOutCubic));
    yield* waitFor(0.34);
  }

  yield* waitFor(2.6);

  yield* all(
    painGroup().opacity(0, 0.4, easeOutCubic),
    head().opacity(0, 0.4, easeOutCubic),
    kicker().opacity(0, 0.4, easeOutCubic),
  );

  yield* all(oldLabel().opacity(1, 0.4, easeOutCubic), oldLabel().y(-140, 0.4, easeOutCubic));
  yield* strike().width(560, 0.34, easeOutCubic);
  yield* all(arrow().opacity(1, 0.3, easeOutCubic), arrow().y(-20, 0.3, easeOutCubic));
  yield* all(
    newLabel().opacity(1, 0.42, easeOutExpo),
    newLabel().scale(1, 0.5, easeOutExpo),
    newSub().opacity(1, 0.5, easeOutCubic),
  );
  yield* waitFor(1.9);
});
