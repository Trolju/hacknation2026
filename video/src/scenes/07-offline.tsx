import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, easeOutCubic, waitFor} from '@revideo/core';
import {Backdrop, Headline, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

export default makeScene2D('07-offline', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const card = createRef<Rect>();
  const alt = createRef<Rect>();
  const foot = createRef<Txt>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'WARUNKI BRZEGOWE'} x={-620} y={-430} />);
  view.add(
    <Headline
      ref={head}
      text={'Bez internetu. Bez chmury. Bez wielkiego LLM-a.'}
      x={-620}
      y={-330}
      size={56}
      width={1560}
    />,
  );

  view.add(
    <Rect
      ref={card}
      x={-70}
      y={30}
      width={1100}
      height={250}
      radius={20}
      fill={'#0C1524'}
      stroke={COLORS.green}
      lineWidth={1.5}
      layout={false}
      opacity={0}
    >
      <Txt
        text={'MODEL DOMYŚLNY'}
        x={-500}
        y={-78}
        offsetX={-1}
        fill={COLORS.green}
        fontFamily={FONT}
        fontSize={17}
        fontWeight={700}
        letterSpacing={2.6}
      />
      <Txt
        text={'Bielik-11B-v2.3-Instruct  ·  Q4_K_M'}
        x={-500}
        y={-14}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={40}
        fontWeight={700}
        letterSpacing={-0.8}
      />
      <Txt
        text={'6,7 GB  ·  llama.cpp albo Ollama  ·  jeden serwer w urzędzie, zero wywołań na zewnątrz'}
        x={-500}
        y={62}
        offsetX={-1}
        offsetY={-0.5}
        width={1000}
        textWrap
        textAlign={'left'}
        fill={COLORS.muted}
        fontFamily={FONT}
        fontSize={22}
        fontWeight={400}
        lineHeight={32}
      />
    </Rect>,
  );

  view.add(
    <Rect
      ref={alt}
      x={-70}
      y={230}
      width={1100}
      height={86}
      radius={16}
      fill={'#0A1220'}
      stroke={'#1E2C42'}
      lineWidth={1.5}
      layout={false}
      opacity={0}
    >
      <Txt
        text={'Alternatywa:  Qwen2.5-7B-Instruct  ·  4,7 GB  —  gdy brakuje GPU'}
        x={-500}
        offsetX={-1}
        fill={COLORS.muted}
        fontFamily={FONT}
        fontSize={23}
        fontWeight={500}
      />
    </Rect>,
  );

  view.add(
    <Txt
      ref={foot}
      text={
        'Tryb demo nie potrzebuje żadnego modelu: MODULE_MODE_DEFAULT=fake działa na danych testowych.'
      }
      x={-620}
      y={370}
      offsetX={-1}
      offsetY={-0.5}
      width={1560}
      textWrap
      textAlign={'left'}
      fill={COLORS.dim}
      fontFamily={FONT}
      fontSize={22}
      fontWeight={400}
      lineHeight={32}
      opacity={0}
    />,
  );

  yield* all(kicker().opacity(1, 0.4), head().opacity(1, 0.6, easeOutCubic));
  yield* all(card().opacity(1, 0.5, easeOutCubic), card().y(0, 0.5, easeOutCubic));
  yield* all(alt().opacity(1, 0.45, easeOutCubic), alt().y(200, 0.45, easeOutCubic));
  yield* foot().opacity(1, 0.6, easeOutCubic);
  yield* waitFor(9.0);
});
