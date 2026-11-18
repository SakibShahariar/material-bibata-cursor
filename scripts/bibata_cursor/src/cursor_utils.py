#!/usr/bin/env python

import sys
import argparse
import logging
import subprocess
import tomllib
import json
import re
import zipfile

from typing import Any
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger()

DEFAULT_THEMES = [
    'Bibata-Modern-Classic',
    'Bibata-Modern-Ice',
    'Bibata-Modern-Amber',
]

XCURSOR_LINK_MAP = {
    'none': [],
    'all': [],
    'spec': [
        'alias', 'all-scroll', 'cell', 'col-resize', 'context-menu', 'copy', 'crosshair',
        'default', 'default', 'e-resize', 'ew-resize', 'help', 'n-resize', 'ne-resize',
        'nesw-resize', 'no-drop', 'not-allowed', 'ns-resize', 'nw-resize', 'nwse-resize',
        'pointer', 'progress', 'row-resize', 's-resize', 'se-resize', 'sw-resize', 'text',
        'up-arrow', 'vertical-text', 'w-resize', 'wait'
    ],
    'adwaita': [
        'alias', 'all-scroll', 'arrow', 'bd_double_arrow', 'bottom_left_corner',
        'bottom_right_corner', 'bottom_side', 'cell', 'col-resize', 'context-menu', 'copy',
        'cross', 'cross_reverse', 'crosshair', 'default', 'diamond_cross', 'dnd-move',
        'e-resize', 'ew-resize', 'fd_double_arrow', 'fleur', 'grab', 'grabbing', 'hand1',
        'hand2', 'help', 'left_ptr', 'left_side', 'move', 'n-resize', 'ne-resize',
        'nesw-resize', 'no-drop', 'not-allowed', 'ns-resize', 'nw-resize', 'nwse-resize',
        'pointer', 'progress', 'question_arrow', 'right_side', 'row-resize', 's-resize',
        'sb_h_double_arrow', 'sb_v_double_arrow', 'se-resize', 'sw-resize', 'tcross', 'text',
        'top_left_arrow', 'top_left_corner', 'top_right_corner', 'top_side', 'vertical-text',
        'w-resize', 'wait', 'watch', 'xterm', 'zoom-in', 'zoom-out'
    ],
}  # fmt: skip


class Utils:
    @classmethod
    def config_logging(cls, loglevel: int | str = logging.DEBUG):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(loglevel)
        console_handler.setFormatter(
            logging.Formatter(
                fmt='{asctime}.{msecs:03.0f} {levelname[0]}: {message}',
                style='{',
                datefmt='%H%M%S',
            )
        )

        logger = logging.getLogger()
        logger.setLevel(loglevel)
        logger.addHandler(console_handler)

    @classmethod
    def run(cls, cmd: str | list[str], *, wait: bool = False, **kwargs) -> subprocess.Popen:
        p = subprocess.Popen(cmd, shell=isinstance(cmd, str), **kwargs)
        if p and wait:
            p.wait()
        return p

    @classmethod
    def traverse_dir(cls, rootdir: Path, depth_limit: int = 8) -> Iterable[Path]:
        for path in rootdir.iterdir():
            if path.is_file():
                yield path
            elif path.is_dir() and depth_limit > 0:
                yield from Utils.traverse_dir(path, depth_limit - 1)

    @classmethod
    def zip_dir(cls, cdir: Path, out: Path):
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for item in cls.traverse_dir(cdir):
                zipf.write(item, arcname=item.relative_to(cdir))

    @classmethod
    def svg_convert(cls, src: Path, dst: Path, width: int = 0, height: int = 0):
        cmd = ['rsvg-convert', '-a']

        if dst.suffix == '.svg':
            cmd.extend(['-f', 'svg'])
        elif dst.suffix == '.png':
            cmd.extend(['-f', 'png'])
        else:
            logger.error(f'svg: invalid convert: {src} -> {dst}')
            return

        if width > 0:
            cmd.extend(['-w', str(width)])
        if height > 0:
            cmd.extend(['-h', str(height)])

        cmd.extend(['-o', str(dst), str(src)])
        cls.run(cmd, wait=True)

    @classmethod
    def svg_recolor(cls, color_maps: list[dict], src: Path, dst: Path):
        svg_data = src.read_text()
        for cmap in color_maps:
            svg_data = svg_data.replace(cmap['match'], cmap['replace'])

        if not dst.parent.is_dir():
            dst.parent.mkdir(parents=True, exist_ok=True)

        dst.write_text(svg_data)

    @classmethod
    def gen_res_symlinks(cls, dst_dir: str, src_dirs: list[str], src_prefix=''):
        dst = Path(dst_dir)
        if not dst.is_dir():
            dst.mkdir(parents=True)

        logger.info(f'symlink for `{dst_dir}`:')
        for src_dir in src_dirs:
            for item in Path(src_prefix + src_dir).iterdir():
                link = dst / item.name
                if link.exists():
                    link.unlink()

                logger.debug(f'-> {link.name} ..')
                link.symlink_to(item.relative_to(dst, walk_up=True))


@dataclass
class CursorRender:
    name: str
    desc: str
    dir: str
    color_maps: list[dict[str, str]]


@dataclass
class HyprManifest:
    name: str
    description: str
    version: str = '0.1'
    directory: str = 'hyprcursors'

    def dumps(self):
        lines = []
        lines.append(f'name = {self.name}')
        lines.append(f'description = {self.description}')
        lines.append(f'version = {self.version}')
        lines.append(f'cursors_directory = {self.directory}')
        return '\n'.join(lines)

    def write(self, cdir: str = ''):
        dirPath = cdir if cdir else self.name
        Path(f'{dirPath}/{self.directory}').mkdir(parents=True, exist_ok=True)
        Path(f'{dirPath}/manifest.hl').write_text(self.dumps())


@dataclass
class XManifest:
    name: str
    description: str
    directory: str = 'cursors'

    def dumps(self):
        lines = []
        lines.append('[Icon Theme]')
        lines.append(f'Name={self.name}')
        lines.append(f'Comment={self.description}')
        lines.append('Inherits=hicolor')
        return '\n'.join(lines)

    def write(self, cdir: str = ''):
        dirPath = cdir if cdir else self.name
        Path(f'{dirPath}/{self.directory}').mkdir(parents=True, exist_ok=True)
        Path(f'{dirPath}/index.theme').write_text(self.dumps())


@dataclass
class CursorMeta:
    name: str
    resize: str = 'none'  # ^(bilinear)|(nearest)|(none)$
    hotX: float = 0.0  # [0.0, 1.0]
    hotY: float = 0.0  # [0.0, 1.0]
    overrides: list[str] = field(default_factory=list)
    sizes: list[tuple] = field(default_factory=list)
    renders: list[tuple[Path, str, int]] = field(default_factory=list)

    def dumps(self):
        lines = []
        lines.append(f'resize_algorithm = {self.resize}')
        lines.append(f'hotspot_x = {self.hotX:.2f}')
        lines.append(f'hotspot_y = {self.hotY:.2f}')

        if self.overrides:
            lines.append('')
            lines.extend(f'define_override = {x}' for x in self.overrides)

        if self.sizes:
            lines.append('')
            lines.extend(
                'define_size = {}'.format(', '.join([str(x) for x in item]))
                for item in self.sizes
            )

        return '\n'.join(lines)

    def dumpsX(self):
        lines = []
        for item in self.sizes:
            size, dst, delay = (item + (0,))[:3]

            hotX = int(size * self.hotX)
            hotY = int(size * self.hotY)

            line = f'{size} {hotX} {hotY} {dst}'
            if delay > 0:
                line += f' {delay}'
            lines.append(line)

        return '\n'.join(lines)

    def write(self, cdir: str = '', fmt: str = 'hypr'):
        dirPath = cdir if cdir else self.name
        Path(dirPath).mkdir(exist_ok=True)

        if fmt == 'hypr':
            Path(f'{dirPath}/meta.hl').write_text(self.dumps())
        elif fmt == 'x11':
            Path(f'{dirPath}/meta.x11').write_text(self.dumpsX())

    def render(self, render: CursorRender, cdir: str = ''):
        dirPath = cdir if cdir else self.name
        for src, basename, size in self.renders:
            dst = Path(f'{dirPath}/{basename}')

            if dst.suffix == '.svg':
                Utils.svg_recolor(render.color_maps, src, dst)
            elif dst.suffix == '.png':
                tmp = Path('/tmp/.cursor.0248.svg')
                Utils.svg_recolor(render.color_maps, src, tmp)
                Utils.svg_convert(tmp, dst, size, size)
                tmp.unlink()
            else:
                logger.warning(f'cursor `{self.name}`: undefined render suffix: {dst}')

    def post_process(self, cdir: str = '', fmt: str = 'hypr'):
        dirPath = cdir if cdir else self.name
        if fmt == 'hypr':
            Utils.zip_dir(Path(dirPath), Path(dirPath + '.hlc'))
        elif fmt == 'x11':
            Utils.run(
                ['xcursorgen', '-p', dirPath, f'{dirPath}/meta.x11', f'{dirPath}.xcur'],
                wait=True,
                stdout=subprocess.DEVNULL,
            )

    def post_setup(self, cdir: str = '', fmt: str = 'hypr', link: str = 'none'):
        dirPath = cdir if cdir else self.name
        Utils.run(['rm', '-rf', dirPath], wait=True)
        if fmt == 'x11':
            path = Path(f'{dirPath}.xcur').rename(dirPath)
            self.post_x11_symlink(str(path.parent), link)

    def post_x11_symlink(self, cdir: str, link: str):
        dirPath = cdir if cdir else '.'
        for name in self.overrides:
            if link == 'all' or name in XCURSOR_LINK_MAP[link]:
                Path(f'{dirPath}/{name}').symlink_to(self.name)
                logger.debug(f'symlink: {name} -> {self.name}')

    def scan_size_and_render(
        self, refDir: str, sizes: list[int], delay: int = 0, suffix: str = 'svg'
    ):
        self.sizes.clear()
        self.renders.clear()

        renderRef = [
            path
            for path in Utils.traverse_dir(Path(refDir))
            if re.fullmatch(f'{self.name}([_-][0-9]+)?', path.stem)
        ]

        if len(renderRef) == 0:
            logger.warning(f'cursor `{self.name}`: no renderRef')

        if suffix == 'svg':
            sizes = [0]  # for hyprcursor with svg, size is ignored

        for size in sizes:
            basename = f'{self.name}_{size}' if size > 0 else self.name
            for seq, src in enumerate(renderRef):
                dst = basename
                if len(renderRef) > 1:
                    dst += f'_{seq:02}'
                dst += f'.{suffix}'

                if len(renderRef) > 1 and delay > 0:
                    self.sizes.append((size, dst, delay))
                else:
                    self.sizes.append((size, dst))

                self.renders.append((src, dst, size))


class CursorBuilder:
    res_symlink: dict[str, list]  # resource symlink map
    theme: dict[str, dict]  # cursor theme, color map
    config: dict[str, dict]  # left cursor
    config_right: dict[str, dict]  # right cursor

    doSetup: bool = True
    renderList: list[str] = DEFAULT_THEMES
    x11Symlink: str = 'none'
    outDir: str = 'out'

    def __init__(self):
        self.load_config()

    def parse_args(self, argv: list[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog='cursor_utils',
            description='utils to create hypr/X cursor for bibata cursor themes',
        )

        parser.add_argument('--no-setup', help='skip post setup', action='store_true')
        parser.add_argument('--hypr', help='build hypr cursor theme', action='store_true')
        parser.add_argument('--x11', help='build x11 cursor theme', action='store_true')

        parser.add_argument(
            '--x11-symlink',
            help='symlink policy for x11 cursor theme',
            choices=XCURSOR_LINK_MAP.keys(),
            default='adwaita',
        )
        parser.add_argument(
            '--theme', help='which theme to build, ref: `render.json`', default=''
        )
        parser.add_argument('--out-dir', help='output dir', default='./out')
        parser.add_argument(
            '--log-level',
            help='change log level',
            choices=['error', 'warn', 'info', 'debug'],
            default='info',
        )

        return parser.parse_args(argv)

    def load_config(self):
        with Path('./config/build.toml').open('rb') as f:
            self.config = tomllib.load(f)

        with Path('./config/build.right.toml').open('rb') as f:
            self.config_right = tomllib.load(f)

        with Path('./svg/symlink.toml').open('rb') as f:
            self.res_symlink = tomllib.load(f)

        with Path('./config/render.json').open('rb') as f:
            self.theme = json.load(f)

    def get_cursor_config(self, *, right: bool = False) -> tuple[dict, dict]:
        config = self.config_right if right else self.config
        return (config['cursors'], config['cursor_defaults'])

    def get_renders(self) -> Iterable[CursorRender]:
        for name in self.renderList:
            if name not in self.theme:
                continue

            spec = self.theme[name]
            res_dir = f'{self.outDir}/{spec["dir"]}'

            if not Path(res_dir).exists():
                dir_name = spec['dir'].split('/')[-1]
                Utils.gen_res_symlinks(res_dir, self.res_symlink[dir_name], src_prefix='svg/')

            yield CursorRender(name, spec['desc'], res_dir, spec['colors'])

    def get_cursors(self, render: CursorRender, fmt: str = 'hypr') -> Iterable[CursorMeta]:
        cursor_configs, fallback = self.get_cursor_config(
            right=render.name.endswith('-Right')
        )

        if 'x11_name' in fallback:
            logger.warning('fallback has x11_name: {}'.format(fallback.pop('x11_name')))

        def getValue(params: dict, key: str, default: Any):
            return params[key] if key in params else fallback.get(key, default)

        for name, params in cursor_configs.items():
            x11_name = params.get('x11_name', '')

            if not x11_name:
                logger.debug(f'skip cursor `{name}`: no x11_name')
                continue

            hotX = getValue(params, 'x_hotspot', 0) / 256
            hotY = getValue(params, 'y_hotspot', 0) / 256

            x11_symlinks = getValue(params, 'x11_symlinks', [])
            x11_sizes = getValue(params, 'x11_sizes', [])
            x11_delay = getValue(params, 'x11_delay', 0)

            cursor = CursorMeta(name=x11_name, hotX=hotX, hotY=hotY, overrides=x11_symlinks)
            cursor.scan_size_and_render(
                render.dir, x11_sizes, x11_delay, 'svg' if fmt == 'hypr' else 'png'
            )
            yield cursor

    def gen_cursor(self, render: CursorRender, fmt: str = 'hypr'):
        logger.info(f'== {render.name} ({fmt})')

        Manifest = HyprManifest if fmt == 'hypr' else XManifest

        cThemeDir = f'{self.outDir}/{render.name}'
        manifest = Manifest(name=render.name, description=render.desc)
        manifest.write(cThemeDir)

        for cursor in self.get_cursors(render, fmt):
            logger.info(f'- {render.name}/{cursor.name} ..')
            cdir = f'{cThemeDir}/{manifest.directory}/{cursor.name}'

            cursor.write(cdir, fmt)
            cursor.render(render, cdir)
            cursor.post_process(cdir, fmt)
            if self.doSetup:
                cursor.post_setup(cdir, fmt, self.x11Symlink)

    def build(self, fmt: str = 'hypr'):
        for render in self.get_renders():
            self.gen_cursor(render, fmt)

    def run(self, argv: list[str]):
        try:
            args = self.parse_args(argv)
        except Exception as e:
            print(f'** failed to parse args: {e}')
            return

        Utils.config_logging(args.log_level.upper())

        self.doSetup = not args.no_setup
        self.x11Symlink = args.x11_symlink
        self.outDir = args.out_dir

        if Path(self.outDir).exists():
            logger.error(f'output dir `{self.outDir}` already exist, abort')
            return

        if args.theme:
            self.renderList = [args.theme]

        if not args.hypr and not args.x11:
            logger.error('requre at least one of `hypr` or `x11`')
            return

        if args.hypr:
            self.build('hypr')
        if args.x11:
            self.build('x11')


if __name__ == '__main__':
    builder = CursorBuilder()
    builder.run(sys.argv[1:] or ['-h'])
