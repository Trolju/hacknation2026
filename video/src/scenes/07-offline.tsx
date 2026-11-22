import {makeScene2D, Rect, Txt} from '@revideo/2d';
import {all, createRef, delay, easeOutCubic, easeOutExpo, waitFor} from '@revideo/core';
import {Backdrop, Kicker} from '../components';
import {COLORS, FONT} from '../theme';

const LEFT = -840;

const RULES = [
  {t: 'Zero automatycznej wysyłki', d: 'Pismo wychodzi tylko wtedy, gdy urzędnik je zatwierdzi.', c: COLORS.green},
  {t: 'Brak integracji z SIDAS', d: 'Narzędzie wsparcia obok systemu, nie zamiennik procedury.', c: COLORS.blue},
  {t: 'Anonimizacja przed przetwarzaniem', d: 'Dane osobowe usuwane, zanim tekst trafi do modelu.', c: COLORS.red},
];

export default makeScene2D('07-offline', function* (view) {
  const kicker = createRef<Rect>();
  const head = createRef<Txt>();
  const rows = RULES.map(() => createRef<Rect>());
  const card = createRef<Rect>();

  view.add(<Backdrop />);
  view.add(<Kicker ref={kicker} text={'BEZPIECZEŃSTWO'} x={LEFT - 40} y={-400} color={COLORS.green} />);
  view.add(
    <Txt
      ref={head}
      text={'Dane nie wychodzą z urzędu.'}
      x={LEFT}
      y={-330}
      offsetX={-1}
      offsetY={-0.5}
      width={900}
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
    <Rect layout={false}>
      {RULES.map((r, i) => (
        <Rect ref={rows[i]} key={r.t} x={LEFT} y={-30 + i * 176} width={880} layout={false} opacity={0}>
          <Rect width={4} height={92} radius={2} fill={r.c} x={0} y={0} />
          <Txt
            text={r.t}
            x={28}
            y={-20}
            offsetX={-1}
            offsetY={-0.5}
            fill={COLORS.text}
            fontFamily={FONT}
            fontSize={36}
            fontWeight={700}
            letterSpacing={-0.5}
          />
          <Txt
            text={r.d}
            x={28}
            y={26}
            offsetX={-1}
            offsetY={-0.5}
            width={820}
            textWrap
            textAlign={'left'}
            fill={COLORS.muted}
            fontFamily={FONT}
            fontSize={24}
            fontWeight={400}
            lineHeight={33}
          />
        </Rect>
      ))}
    </Rect>,
  );

  view.add(
    <Rect
      ref={card}
      x={470}
      y={60}
      width={820}
      height={500}
      radius={22}
      fill={'#0A1220'}
      stroke={'#243449'}
      lineWidth={1.5}
      layout={false}
      opacity={0}
      scale={0.96}
    >
      <Rect width={720} height={4} radius={2} fill={COLORS.violet} y={-195} />
      <Txt
        text={'MODEL LOKALNY'}
        x={-340}
        y={-150}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.violet}
        fontFamily={FONT}
        fontSize={17}
        fontWeight={700}
        letterSpacing={3}
      />
      <Txt
        text={'Bielik 11B v2.3 Instruct'}
        x={-340}
        y={-96}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={40}
        fontWeight={700}
        letterSpacing={-0.9}
      />
      <Txt
        text={'Q4_K_M  ·  6,7 GB  ·  llama.cpp / Ollama'}
        x={-340}
        y={-44}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.muted}
        fontFamily={FONT}
        fontSize={22}
        fontWeight={400}
      />
      <Rect width={680} height={1} fill={'#1E2A3D'} y={-6} />
      <Txt
        text={'Bez internetu. Bez chmury. Bez wysyłki.'}
        x={-340}
        y={44}
        offsetX={-1}
        offsetY={-0.5}
        fill={COLORS.text}
        fontFamily={FONT}
        fontSize={26}
        fontWeight={600}
      />
      <Txt
        text={'Model da się podmienić w ustawieniach — chmura na czas testów, lokalny Bielik na produkcję.'}
        x={-340}
        y={112}
        offsetX={-1}
        offsetY={-0.5}
        width={680}
        textWrap
        textAlign={'left'}
        fill={COLORS.dim}
        fontFamily={FONT}
        fontSize={20}
        fontWeight={400}
        lineHeight={29}
      />
    </Rect>,
  );

  yield* all(kicker().opacity(1, 0.4, easeOutCubic), kicker().x(LEFT, 0.5, easeOutCubic));
  yield* all(head().opacity(1, 0.5, easeOutCubic), head().y(-322, 0.5, easeOutCubic));

  yield* all(
    ...RULES.map((_, i) =>
      delay(
        i * 0.22,
        all(rows[i]().opacity(1, 0.4, easeOutCubic), rows[i]().x(LEFT + 24, 0.45, easeOutCubic)),
      ),
    ),
  );

  yield* all(card().opacity(1, 0.5, easeOutCubic), card().scale(1, 0.55, easeOutExpo));
  yield* waitFor(3.6);
});
