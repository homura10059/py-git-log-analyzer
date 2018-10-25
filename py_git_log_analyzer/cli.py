# -*- coding: utf-8 -*-
"""
コマンドライン引数を受け取るアプリケーションとして実行するためのコード
"""
import click


@click.group()
def cmd():
    pass


@cmd.command()
@click.option('--path', required=True, help="repos path.")
def create_report(path):
    # FIXME: add logic
    pass


def main():
    cmd()


if __name__ == '__main__':
    main()
