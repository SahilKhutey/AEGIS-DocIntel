/**
 * Build-time Production Authentication Guard (PROT-04 / WP-04.02)
 * Ensures no development tokens, admin bypasses, or prohibited credentials
 * exist in the client-side bundle or environment validation schema.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SRC_DIR = path.resolve(__dirname, '../src');

const PROHIBITED_PATTERNS = [
  {
    pattern: /NEXT_PUBLIC_AEGIS_DEV_TOKEN/,
    description: 'Banned dev-token environment variable in client code',
  },
  {
    pattern: /"dev-default-tenant"/,
    description: 'Banned hardcoded default tenant bypass fallback',
  },
  {
    pattern: /"dev-user"/,
    description: 'Banned development user fallback in client code',
  },
  {
    pattern: /"dev@aegis\.corp"/,
    description: 'Banned development email identity in client code',
  },
  {
    pattern: /"aegis-dev-key"/,
    description: 'Banned development API key in client code',
  },
  {
    pattern: /role:\s*["']admin["']\s*,[\s\S]*?permissions:\s*getPermissionsForRole\(["']admin["']\)/,
    description: 'Banned automatic admin privilege escalation in token resolution',
  },
];

function scanDirectory(dir, issues = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== '__tests__' && entry.name !== 'node_modules') {
        scanDirectory(fullPath, issues);
      }
    } else if (entry.isFile() && /\.(tsx?|jsx?)$/.test(entry.name)) {
      const content = fs.readFileSync(fullPath, 'utf-8');
      for (const { pattern, description } of PROHIBITED_PATTERNS) {
        if (pattern.test(content)) {
          issues.push({
            file: fullPath,
            description,
          });
        }
      }
    }
  }

  return issues;
}

console.log('Running PROT-04 Production Authentication Guard...');
const violations = scanDirectory(SRC_DIR);

if (violations.length > 0) {
  console.error('\n❌ BUILD-TIME SECURITY GUARD FAILURE: Prohibited development auth patterns detected!');
  for (const v of violations) {
    console.error(`  - ${v.file}: ${v.description}`);
  }
  process.exit(1);
}

console.log('✅ PROT-04 Guard Passed: No development tokens or auth bypasses found in web/src.');
process.exit(0);
