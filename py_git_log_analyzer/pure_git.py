# -*- coding: utf-8 -*-
"""
pure な git log 解析用
"""
import git
import re
import os
import pandas as pd
from git import InvalidGitRepositoryError
from pandas import DataFrame
from pathlib import Path


def list_from(commit_message: str, project_name: str)-> list:
    """
    1 commit message を file ごとの commit 情報 list に変換する

    commit_info = {
        'project_name': str,
        'author': str,
        'date': str,
        'plus_line_count': int,
        'minus_line_count': int,
        'file': str,
    }

    :param commit_message:
    :param project_name:
    :return:
    """
    messages = commit_message.split('\n')

    author = None
    date = None

    pattern = '"(.+)__(.+)"'
    result = re.match(pattern, messages[0])
    if result:
        author = result.group(1)
        date = result.group(2)

    result_list = []
    for message in messages:
        if "\t" in message:
            line_counts = message.split("\t")
            plus = 0
            if line_counts[0] != '-':
                plus = int(line_counts[0])
            minus = 0
            if line_counts[1] != '-':
                minus = int(line_counts[1])
            commit_info = {
                'project_name': project_name,
                'author': author,
                'date': date,
                'plus_line_count': plus,
                'minus_line_count': minus,
                'file': line_counts[2],
            }
            result_list.append(commit_info)

    return result_list


def data_flame_from(path: str)-> DataFrame:
    """
    path に存在する git リポジトリの log を DataFlame に変換する
    :param path:
    :return: DataFrame
    """
    commit_list = commit_log_list_in(path)
    df = pd.DataFrame(commit_list)
    df['total_line_count'] = df['plus_line_count'] + df['minus_line_count']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    df_multi = df.set_index([df.index.year, df.index.quarter, df.index.month, df.index.weekday, df.index])
    df_multi.index.names = ['year', 'quarter', 'month', 'weekday', 'date']
    df_multi.sort_index(inplace=True)
    return df_multi


def data_flame_under(base_dir_path: str)-> DataFrame:
    """
    base_dir_path 配下のすべての git リポジトリの log を統合して一つの DataFlame に変換する
    :param base_dir_path:
    :return: DataFrame
    """
    p = Path(base_dir_path).resolve()
    sub_dirs = [x for x in p.iterdir() if x.is_dir()]
    commit_list = []
    for sub_dir in sub_dirs:
        commit_list.extend(commit_log_list_in(str(sub_dir)))
    df = pd.DataFrame(commit_list)
    df['total_line_count'] = df['plus_line_count'] + df['minus_line_count']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    df_multi = df.set_index([df.index.year, df.index.quarter, df.index.month, df.index.weekday, df.index])
    df_multi.index.names = ['year', 'quarter', 'month', 'weekday', 'date']
    df_multi.sort_index(inplace=True)
    return df_multi


def commit_log_list_in(path: str)-> list:
    """
    path に存在するgit
    :param path:
    :return:
    """
    try:
        repo = git.Repo(path)
    except InvalidGitRepositoryError:
        return []

    log = repo.git.log('--numstat', '--date=iso', '--pretty=________"%an__%ad"', '--no-merges')
    working_dir = repo.git.working_dir
    project_name = working_dir.replace(os.sep, '/').split('/')[-1]
    commit_logs = log.split('________')
    commit_logs.pop(0)  # 最初の行は空文字しか入ってないので除く

    commit_log_list = []
    for commit_log in commit_logs:
        tmp_list = list_from(commit_log, project_name)
        commit_log_list.extend(tmp_list)

    return commit_log_list
