import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('png');
Config.setOverwriteOutput(true);
// локальный Chrome: скачивание headless-shell обрывается (ECONNRESET)
Config.setBrowserExecutable(
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
);
