# -*- coding: utf-8 -*-
"""
git-lab log 解析用
"""

from pathlib import Path

import pandas as pd
from gitlab import Gitlab
from gitlab.v4.objects import MergeRequest
from pandas import DataFrame


class GitlabUtil:
    """
    Gitlab に足りないメソッドを補うために仕方なく作ったクラス
    """

    def __init__(self, gl: Gitlab):
        self.gl = gl

    @staticmethod
    def get_all_item(listed, **kwargs) -> list:
        """
        list() メソッドを持つオブジェクトに対して、 list() を全てのページに対して実行した結果を取得する.
        :param listed:
        :param kwargs:
        :return: list
        """
        page_count = 1
        item_in_page = 1
        all_item = []
        while item_in_page > 0:
            listed_item = listed.list(page=page_count, **kwargs)
            all_item.extend(listed_item)
            page_count += 1
            item_in_page = len(listed_item)
        return all_item

    def all_group_under(self, root_group_id: str, **kwargs) -> list:
        """
        root_group_id 下の全てのグループを取得する
        :param root_group_id:
        :return: list
        """
        group = self.gl.groups.get(root_group_id)
        subgroups = self.get_all_item(group.subgroups, **kwargs)
        return subgroups

    def all_project_under(self, group_id: str, **kwargs) -> list:
        """
        group_id 下の全てのプロジェクトを取得する
        :param group_id:
        :return: list
        """
        group = self.gl.groups.get(group_id)
        projects = self.get_all_item(group.projects, **kwargs)
        return projects

    def all_mr_under(self, project_id: str, **kwargs) -> list:
        """
        project_id 下の全ての MR を取得します
        :param project_id:
        :param kwargs:
        :return:
        """
        project = self.gl.projects.get(project_id)
        mrs = self.get_all_item(project.mergerequests, **kwargs)
        return mrs


class GitlabAnalyzer:
    """
    Gitlab の log を取得・分析するためのクラス
    """

    def __init__(self, gl: Gitlab):
        self.util = GitlabUtil(gl)
        self.gl = self.util.gl

    def get_discussion_comment(self, mr: MergeRequest, project_name: str) -> list:
        """
        mr の discussion_comment を全て取得する
        :param mr:
        :param project_name:
        :return: list
        """
        author_id = mr.author['id']
        discussions = self.util.get_all_item(mr.discussions)
        discussion_comments = []
        for discussion in discussions:
            if not discussion.individual_note:
                for note in discussion.attributes['notes']:
                    if not note['author']['id'] == author_id and not note['system']:
                        discussion_comment = {
                            "created_at": note['created_at'],
                            "project_name": project_name,
                            "author_id": mr.author['id'],
                            "reviewer_id": note['author']['id'],
                            "resolvable": note['resolvable'],
                            "body": note['body'].strip()
                        }
                        discussion_comments.append(discussion_comment)
        return discussion_comments

    def get_discussion_comment_in(self, project_id: str, created_after: str = None) -> list:
        """
        project_id の discussion_comment を取得する.
        created_after が指定されればそれ以降の日時で取得する.
        :param project_id:
        :param created_after:
        :return:
        """
        project = self.gl.projects.get(project_id)
        print(project.name + ": start")
        mrs = self.util.all_mr_under(project_id, state='merged', order_by='updated_at',
                                     created_after=created_after)
        discussion_comments = []
        for mr in mrs:
            comments_per_mr = self.get_discussion_comment(mr, project.name)
            discussion_comments.extend(comments_per_mr)
        return discussion_comments

    def get_discussion_comment_df_from(self, project_id: str,
                                       data_folder_path: str = "data/git-lab/mr-comments") -> DataFrame:
        """
        project_id の discussion_comment を取得する.
        data_folder_path 以下にキャッシュを取り、2回目以降はキャッシュに無いものを取得する.
        :param project_id:
        :param data_folder_path:
        :return:
        """
        path = Path(data_folder_path) / "{}.csv".format(project_id)
        if path.exists():
            print("    cache hit!" + str(path.resolve()))
            df = pd.read_csv(str(path.resolve()), encoding="utf-8")
            # cache を更新する
            comments = self.get_discussion_comment_in(project_id, created_after=str(df['created_at'].max()))
            df_new = self.data_flame_from(comments)
            df.append(df_new)
            if df.size > 0:
                df.to_csv(str(path.resolve()), encoding="utf-8", index=False)
            return df
        else:
            print("    no hit:" + str(path.resolve()))
            comments = self.get_discussion_comment_in(project_id)
            df = self.data_flame_from(comments)
            if df.size > 0:
                df.to_csv(str(path.resolve()), encoding="utf-8", index=False)

            return df

    @staticmethod
    def data_flame_from(comments: list) -> DataFrame:
        """
        List を DataFlame に変換する
        :param comments:
        :return:
        """
        df = pd.DataFrame(comments)
        if df.size > 0:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    def get_commit_info_in(self, project_id, created_after: str = None) -> list:
        """
        project_id の commit 情報を取得する.
        created_after が指定されればそれ以降の日時で取得する.
        :param project_id:
        :param created_after:
        :return:
        """
        project = self.gl.projects.get(project_id)
        commits = self.util.get_all_item(project.commits, ef_name='develop', with_stats=True, since=created_after)
        commit_info_list = []
        for commit in commits:
            if "Merge" not in commit.message:
                commit_info = {
                    'project_name': project.name,
                    'author_name': commit.author_name,
                    'created_at': commit.created_at,
                    'additions': commit.stats['additions'],
                    'deletions': commit.stats['deletions'],
                    'total': commit.stats['total'],
                    'message': commit.message,
                }
                commit_info_list.append(commit_info)
        return commit_info_list

    def get_commit_info_df_from(self, project_id, data_folder_path: str = "data/git-lab/commits") -> DataFrame:
        """
        project_id の commit 情報を取得する.
        data_folder_path 以下にキャッシュを取り、2回目以降はキャッシュに無いものを取得する.
        :param project_id:
        :param data_folder_path:
        :return:
        """
        path = Path(data_folder_path) / "{}.csv".format(project_id)
        if path.exists():
            print("    cache hit!" + str(path.resolve()))
            df = self.to_datetime(pd.read_csv(str(path.resolve()), encoding="utf-8"))
            # cache を更新する
            commit_info_list = self.get_commit_info_in(project_id, created_after=str(df['created_at'].max()))
            df_new = self.to_datetime(pd.DataFrame(commit_info_list))
            df.append(df_new)
            if df.size > 0:
                df.to_csv(str(path.resolve()), encoding="utf-8", index=False)
            return df
        else:
            print("    no hit:" + str(path.resolve()))
            commit_info_list = self.get_commit_info_in(project_id)
            df = self.to_datetime(pd.DataFrame(commit_info_list))
            if df.size > 0:
                df.to_csv(str(path.resolve()), encoding="utf-8", index=False)
            return df

    @staticmethod
    def to_datetime(df: DataFrame) -> DataFrame:
        """
        DataFrame に datetime を設定する
        :param df:
        :return:
        """
        df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    def get_discussion_comment_df_under(self, group_id) -> DataFrame:
        """
        group 配下のプロジェクトの discussion_comment を取得する
        :param group_id:
        :return:
        """
        real_group = self.gl.groups.get(group_id)
        sub_projects = self.util.get_all_item(real_group.projects)
        df_list = []
        for sub_project in sub_projects:
            real_project = self.gl.projects.get(sub_project.id)
            # print(real_project.name + ": start")
            df = self.get_discussion_comment_df_from(real_project.id)
            if df.size > 0:
                df_list.append(df)
            # print(real_project.name + ": finish")

        df_joined = pd.concat(df_list)
        return df_joined

    def get_commit_info_df_under(self, group_id) -> DataFrame:
        """
        group 配下のプロジェクトの commit 情報 を取得する
        :param group_id:
        :return:
        """
        real_group = self.gl.groups.get(group_id)
        sub_projects = self.util.get_all_item(real_group.projects)
        df_list = []
        for sub_project in sub_projects:
            real_project = self.gl.projects.get(sub_project.id)
            # print(real_project.name + ": start")
            df = self.get_commit_info_df_from(sub_project.id)
            if df.size > 0:
                df_list.append(df)
            # print(real_project.name + ": finish")

        df_joined = pd.concat(df_list)
        return df_joined
