import {mkdirSync} from 'node:fs';
import {renderVideo} from '@revideo/renderer';

// Revideo nie tworzy katalogu wyjściowego sam.
mkdirSync('output/out', {recursive: true});

// Ustaw CHROME_PATH, jeśli Puppeteer nie znajdzie własnej przeglądarki.
const executablePath = process.env.CHROME_PATH;

const out = await renderVideo({
  projectFile: './src/project.ts',
  settings: {
    outFile: 'out/asystent.mp4',
    workers: 2,
    logProgress: true,
    puppeteer: {
      ...(executablePath ? {executablePath} : {}),
      args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
    },
  },
});

console.log('OUT', out);
