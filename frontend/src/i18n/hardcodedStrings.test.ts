import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SOURCE_ROOT = join(__dirname, '..');
const CYRILLIC_PATTERN = /[Ѐ-ӿ]/;
const SOURCE_EXTENSION_PATTERN = /\.(ts|tsx)$/;
const TEST_FILE_PATTERN = /\.test\.(ts|tsx)$/;

function listSourceFiles(folder: string): string[] {
  return readdirSync(folder).flatMap((entry) => {
    const path = join(folder, entry);
    if (statSync(path).isDirectory()) {
      return listSourceFiles(path);
    }
    return SOURCE_EXTENSION_PATTERN.test(entry) && !TEST_FILE_PATTERN.test(entry) ? [path] : [];
  });
}

describe('UI strings', () => {
  it('live only in src/i18n/uk.json', () => {
    const offenders = listSourceFiles(SOURCE_ROOT)
      .filter((path) => CYRILLIC_PATTERN.test(readFileSync(path, 'utf8')))
      .map((path) => relative(SOURCE_ROOT, path));

    expect(offenders).toEqual([]);
  });
});
