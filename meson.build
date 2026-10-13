project('assrender', 'c',
  default_options : ['buildtype=release', 'b_ndebug=if-release', 'c_std=c11', 'default_library=static'],
  meson_version : '>=1.1.0',
  version : '0.39.0'
)

cc = meson.get_compiler('c')
host = host_machine.system()

# libass from the system where there is one, otherwise built statically from the subproject (the wheels force that).
# Fonts: fontconfig on Linux, DirectWrite on Windows, CoreText on macOS.
fontconfig = host == 'linux' ? 'enabled' : 'disabled'
libass_dep = dependency('libass', version : '>=0.15.0',
  fallback : ['libass', 'libass_dep'],
  default_options : ['default_library=static', 'asm=disabled', 'fontconfig=' + fontconfig, 'test=disabled',
                     'harfbuzz:tests=disabled', 'harfbuzz:docs=disabled', 'harfbuzz:utilities=disabled',
                     'freetype2:tests=disabled', 'fribidi:tests=false', 'fribidi:docs=false', 'fribidi:bin=false'])

sources = files(
  'src/assrender.c',
  'src/csriapi.c',
  'src/render.c',
  'src/sub.c',
  'src/timecodes.c',
)

link_args = []
if host == 'linux'
  # The statically linked libass and its dependencies stay private to the plugin.
  link_args += ['-Wl,--exclude-libs,ALL']
endif
if host == 'windows'
  if cc.get_argument_syntax() == 'msvc'
    link_args += ['/DEF:' + meson.current_source_dir() / 'src' / 'assrender.def']
  endif
endif

# VapourSynth only autoloads *.dylib on macOS, while Meson defaults to *.so for modules.
suffix = host == 'darwin' ? 'dylib' : []

if get_option('python_package')
  # Same layout as the VapourSynth PyPI package autoloads from: site-packages/vapoursynth/plugins
  py = import('python').find_installation(pure : false)
  install_dir = py.get_install_dir() / 'vapoursynth' / 'plugins'
else
  install_dir = get_option('libdir') / 'vapoursynth'
endif

shared_module('assrender', sources,
  include_directories : include_directories('src', 'src/include'),
  dependencies : libass_dep,
  link_args : link_args,
  install : true,
  install_dir : install_dir,
  name_suffix : suffix,
  gnu_symbol_visibility : 'default'
)
