<?php
/**
 * Extract code context around a file:line, printing a TG-friendly snippet.
 *
 * Usage:
 *   php scripts/extract_code_context.php /abs/path/to/File.php 123 15
 *
 * Output format:
 *   Code(±15):
 *     108| ...
 *   >>123| ...
 */

if ($argc < 3) {
    fwrite(STDERR, "Usage: php extract_code_context.php <file> <line> [radius]\n");
    exit(2);
}

$file = (string)$argv[1];
$line = (int)$argv[2];
$radius = isset($argv[3]) ? (int)$argv[3] : 15;

if ($file === '' || $line <= 0) {
    fwrite(STDERR, "Invalid file/line\n");
    exit(2);
}
if (!is_file($file) || !is_readable($file)) {
    fwrite(STDERR, "File not readable: {$file}\n");
    exit(1);
}

$lines = @file($file, FILE_IGNORE_NEW_LINES);
if (!is_array($lines) || empty($lines)) {
    fwrite(STDERR, "Failed to read: {$file}\n");
    exit(1);
}

$total = count($lines);
$start = max(1, $line - $radius);
$end = min($total, $line + $radius);

function sanitize_code_line(string $line): string {
    $patterns = [
        '/(password\s*[=:]\s*)(["\"][^"\"]+["\"]|\'[^\']+\')/i',
        '/(token\s*[=:]\s*)(["\"][^"\"]+["\"]|\'[^\']+\')/i',
        '/(secret\s*[=:]\s*)(["\"][^"\"]+["\"]|\'[^\']+\')/i',
        '/(authorization\s*[=:]\s*)(["\"][^"\"]+["\"]|\'[^\']+\')/i',
        '/(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*/',
    ];
    foreach ($patterns as $p) {
        $line = preg_replace($p, '$1***', $line);
    }
    return $line;
}

$out = [];
for ($i = $start; $i <= $end; $i++) {
    $prefix = ($i === $line) ? '>>' : '  ';
    $codeLine = sanitize_code_line((string)$lines[$i - 1]);
    $out[] = sprintf('%s%5d| %s', $prefix, $i, $codeLine);
}

echo "Code(±{$radius}):\n" . implode("\n", $out) . "\n";
