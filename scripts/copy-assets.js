const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const STATIC = path.join(ROOT, 'static', 'vendor');

const ASSETS = {
  'admin-lte/dist/css/adminlte.min.css': 'adminlte/css/adminlte.min.css',
  'admin-lte/dist/js/adminlte.min.js': 'adminlte/js/adminlte.min.js',
  'bootstrap/dist/js/bootstrap.bundle.min.js': 'bootstrap/js/bootstrap.bundle.min.js',
  'bootstrap-icons/font/bootstrap-icons.min.css': 'bootstrap-icons/css/bootstrap-icons.min.css',
};

// Bootstrap icons fonts
const FONTS_SRC = path.join(ROOT, 'node_modules', 'bootstrap-icons', 'font', 'fonts');
const FONTS_DST = path.join(STATIC, 'bootstrap-icons', 'fonts');

// Copy CSS/JS files
for (const [srcRel, dstRel] of Object.entries(ASSETS)) {
  const src = path.join(ROOT, 'node_modules', srcRel);
  const dst = path.join(STATIC, dstRel);
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
  console.log(`✓ ${dstRel}`);
}

// Copy font files
if (fs.existsSync(FONTS_SRC)) {
  fs.mkdirSync(FONTS_DST, { recursive: true });
  fs.readdirSync(FONTS_SRC).forEach(file => {
    fs.copyFileSync(path.join(FONTS_SRC, file), path.join(FONTS_DST, file));
    console.log(`✓ bootstrap-icons/fonts/${file}`);
  });
}

console.log('\nDone! Assets copied to static/vendor/');
