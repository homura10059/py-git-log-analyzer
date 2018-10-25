from py_git_log_analyzer.core import list_from, data_flame_from, data_flame_under

"""
pytest 用のテストコード
"""
import os


def test_list_from_commit_message():
    message = '"o-hayato__2018-09-28 18:23:31 +0900"\n\n' \
              '56\t21\tsrc/main/java/com/sample/Sample.java\n' \
              '1\t1\tsrc/main/resources/sample_log.properties\n' \
              '25\t17\tsrc/test/java/com/sample/SampleTest.java\n'
    result_list = list_from(message, "sample")

    for result in result_list:
        assert result['author'] == "o-hayato"
        assert result['date'] == "2018-09-28 18:23:31 +0900"
        assert result['project_name'] == "sample"

    assert result_list[0]['plus_line_count'] == 56
    assert result_list[0]['minus_line_count'] == 21
    assert result_list[0]['file'] == 'src/main/java/com/sample/Sample.java'

    assert result_list[1]['plus_line_count'] == 1
    assert result_list[1]['minus_line_count'] == 1
    assert result_list[1]['file'] == 'src/main/resources/sample_log.properties'

    assert result_list[2]['plus_line_count'] == 25
    assert result_list[2]['minus_line_count'] == 17
    assert result_list[2]['file'] == 'src/test/java/com/sample/SampleTest.java'


def test_data_flame_from():
    path = "./../"
    abspath = os.path.abspath(path)
    df = data_flame_from(abspath)
    print(df.head(10))
    assert df.size != 0


def test_data_flame_under():
    path = "./../../"
    abspath = os.path.abspath(path)
    df = data_flame_under(abspath)
    print(df.head(10))
    assert df.size != 0
