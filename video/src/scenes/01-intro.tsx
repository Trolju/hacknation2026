import {makeScene2D, Rect, Txt} from '@revideo/2d';
import type {Reference} from '@revideo/core';
import {all, createRef, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, EVENT, FONT, TEAM} from '../theme';

const LEFT = -840;
const TITLE_SIZE = 148;
const TITLE_H = TITLE_SIZE * 1.3;

/** Linia tekstu odsłaniana spod maski (wjazd z dołu). */
function MaskLine({
  text,
  y,
  size,
  color,
  weight = 800,
  maskRef,
  textRef,
}: {
  text: string;
  y: number;
  size: number;
  color: string;
  weight?: number;
  maskRef?: Reference<Rect>;
  textRef?: Reference<Txt>;
}) {
  const h = size * 1.3;
  return (
    <Rect ref={maskRef} width={1920} height={h} y={y} clip layout={false}>
      <Txt
        ref={textRef}
        text={text}
        x={LEFT}
        y={-h / 2}
        offsetX={-1}
        offsetY={-0.5}
        fill={color}
        fontFamily={FONT}
        fontSize={size}
        fontWeight={weight}
        letterSpacing={-3.2}
      />
    </Rect>
  );
}

export default makeScene2D('01-intro', function* (view) {
  const kicker = createRef<Rect>();
  const ghost = createRef<Txt>();
  const t1 = createRef<Txt>();
  const t2 = createRef<Txt>();
  const rule = createRef<Rect>();
  const sub = createRef<Txt>();
  const team = createRef<Txt>();
  const stats = createRef<Rect>();

  view.add(<Backdrop />);
  view.add(
    <Txt
      ref={ghost}
      text={'UDIP'}
      x={640}
      y={40}
      fill={'#FFFFFF'}
      opacity={0.045}
      fontFamily={FONT}
      fontSize={400}
      fontWeight={800}
      letterSpacing={-20}
    />,
  );
  view.add(<Kicker ref={kicker} text={EVENT.toUpperCase()} x={LEFT - 40} y={-400} />);
  view.add(<MaskLine text={'Inteligentny'} y={-232} size={TITLE_SIZE} color={COLORS.text} textRef={t1} />);
  view.add(<MaskLine text={'asystent urzędnika'} y={-78} size={148} color={COLORS.text} textRef={t2} />);
  view.add(<Rect ref={rule} width={0} height={4} radius={2} fill={COLORS.blue} x={LEFT} y={44} offsetX={-1} />);
  view.add(
    <Txt
      ref={sub}
      text={'Wniosek wchodzi. Pismo wychodzi. Decyzja zostaje po stronie urzędnika.'}
      x={LEFT}
      y={150}
      offsetX={-1}
      offsetY={-0.5}
      width={1240}
      textWrap
      textAlign={'left'}
      fill={COLORS.muted}
      fontFamily={FONT}
      fontSize={32}
      fontWeight={400}
      lineHeight={46}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={team}
      text={`ZESPÓŁ  ·  ${TEAM.join('  ·  ')}`}
      x={LEFT}
      y={268}
      offsetX={-1}
      offsetY={-0.5}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={21}
      fontWeight={500}
      letterSpacing={1.6}
      opacity={0}
    />,
  );

  const statItems = [
    {v: '8', l: 'modułów'},
    {v: '0', l: 'automatycznych wysyłek'},
    {v: '100%', l: 'danych w urzędzie'},
  ];
  view.add(
    <Rect ref={stats} layout={false} y={430} opacity={0}>
      {statItems.map((s, i) => (
        <Rect key={i} x={LEFT + 40 + i * 420} layout={false}>
          <Txt
            text={s.v}
            x={0}
            y={-14}
            offsetX={-1}
            offsetY={-0.5}
            fill={COLORS.text}
            fontFamily={FONT}
            fontSize={54}
            fontWeight={800}
            letterSpacing={-2}
          />
          <Txt
            text={s.l}
            x={0}
            y={40}
            offsetX={-1}
            offsetY={-0.5}
            fill={COLORS.dim}
            fontFamily={FONT}
            fontSize={19}
            fontWeight={500}
            letterSpacing={0.6}
          />
        </Rect>
      ))}
    </Rect>,
  );

  t1().y(TITLE_H);
  t2().y(TITLE_H);

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(t1().y(-TITLE_H / 2, 0.62, easeOutExpo), ghost().opacity(0.05, 1.2, easeOutCubic));
  yield* all(t2().y(-TITLE_H / 2, 0.62, easeOutExpo), rule().width(150, 0.5, easeOutCubic));
  yield* all(
    sub().opacity(1, 0.5, easeOutCubic),
    sub().y(134, 0.5, easeOutCubic),
    team().opacity(1, 0.5, easeOutCubic),
    stats().opacity(1, 0.6, easeOutCubic),
    stats().y(422, 0.6, easeOutCubic),
  );
  yield* waitFor(3.4);
});
