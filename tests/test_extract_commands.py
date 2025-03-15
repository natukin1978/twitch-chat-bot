import unittest

from extract_commands import extract_commands


class TestExtractCommands(unittest.TestCase):
    def test_extract_commands_basic(self):
        self.assertEqual(extract_commands("/clear"), ["clear"])
        self.assertEqual(extract_commands("/ban hoge"), ["ban", "hoge"])
        self.assertEqual(extract_commands("/timeout hoge 60"), ["timeout", "hoge", "60"])
        self.assertEqual(extract_commands("/command arg1 arg2 arg3 arg4"), ["command", "arg1", "arg2", "arg3", "arg4"])

    def test_extract_commands_no_match(self):
        self.assertEqual(extract_commands("普通のテキスト"), [])
        self.assertEqual(extract_commands(""), [])

    def test_extract_commands_mixed_text(self):
        self.assertEqual(extract_commands("よしやるよ！/ban hoge どうだまいったか。"), ["ban", "hoge"])
        self.assertEqual(extract_commands("/clear 実行する。"), ["clear"])
        self.assertEqual(extract_commands("何か/command arg1 arg2 を実行"), ["command", "arg1", "arg2"])

    def test_extract_commands_edge_cases(self):
        self.assertEqual(extract_commands("/command"), ["command"])
        self.assertEqual(extract_commands("/command "), ["command"])
        self.assertEqual(extract_commands(" /command"), ["command"])
        self.assertEqual(extract_commands("/command arg1  arg2"), ["command", "arg1", "arg2"])
