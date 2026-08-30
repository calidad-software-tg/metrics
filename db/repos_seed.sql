INSERT INTO repos (org, repo, full_name, url, plataforma) VALUES
  ('tldr-pages', 'tldr', 'tldr-pages/tldr', 'https://github.com/tldr-pages/tldr', 'GitHub'),
  ('flutter', 'flutter', 'flutter/flutter', 'https://github.com/flutter/flutter', 'GitHub'),
  ('home-assistant', 'core', 'home-assistant/core', 'https://github.com/home-assistant/core', 'GitHub'),
  ('microsoft', 'vscode', 'microsoft/vscode', 'https://github.com/microsoft/vscode', 'GitHub'),
  ('freeCodeCamp', 'freeCodeCamp', 'freeCodeCamp/freeCodeCamp', 'https://github.com/freeCodeCamp/freeCodeCamp', 'GitHub'),
  ('vercel', 'next.js', 'vercel/next.js', 'https://github.com/vercel/next.js', 'GitHub'),
  ('tensorflow', 'tensorflow', 'tensorflow/tensorflow', 'https://github.com/tensorflow/tensorflow', 'GitHub'),
  ('python', 'cpython', 'python/cpython', 'https://github.com/python/cpython', 'GitHub'),
  ('raysan5', 'raylib', 'raysan5/raylib', 'https://github.com/raysan5/raylib', 'GitHub'),
  ('GNOME', 'gimp', 'GNOME/gimp', 'https://gitlab.gnome.org/GNOME/gimp', 'GitLab')
ON CONFLICT (full_name) DO NOTHING;
