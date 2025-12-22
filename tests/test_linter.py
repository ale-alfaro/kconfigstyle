"""Tests for Kconfig linter functionality."""

import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import KconfigLinter, LinterConfig


class TestZephyrStyle:
    """Test Zephyr style linting."""

    def test_valid_zephyr_file(self):
        """Test that a valid Zephyr file has no issues."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "# Network configuration\n",
            "\n",
            "config NETWORKING\n",
            '\tbool "Enable networking"\n',
            "\thelp\n",
            "\t  Enable network stack support.\n",
            "\n",
            "config NET_IPV4\n",
            '\tbool "IPv4 support"\n',
            "\tdepends on NETWORKING\n",
            "\thelp\n",
            "\t  Enable IPv4 protocol support.\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 0, f"Expected no issues, got: {issues}"
        finally:
            temp_path.unlink()

    def test_trailing_whitespace(self):
        """Test detection of trailing whitespace."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\tbool "Test"  \n',  # Trailing spaces
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "Trailing whitespace" in issues[0].message
            assert issues[0].line_number == 2
        finally:
            temp_path.unlink()

    def test_line_too_long(self):
        """Test detection of lines exceeding max length."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        long_line = "# " + "x" * 100 + "\n"
        lines = [long_line]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "exceeds 100 characters" in issues[0].message
        finally:
            temp_path.unlink()

    def test_spaces_instead_of_tabs(self):
        """Test detection of spaces when tabs are required."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '    bool "Test"\n',  # 4 spaces instead of tab
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "Use tabs for indentation" in issues[0].message
        finally:
            temp_path.unlink()

    def test_comment_without_space(self):
        """Test detection of comments without space after #."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = ["#Bad comment\n"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "space after #" in issues[0].message
        finally:
            temp_path.unlink()

    def test_help_text_indentation(self):
        """Test help text indentation checking."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\tbool "Test"\n',
            "\thelp\n",
            "\tWrong indentation.\n",  # Should be tab + 2 spaces
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "Help text should be indented" in issues[0].message
        finally:
            temp_path.unlink()


class TestESPIDFStyle:
    """Test ESP-IDF style linting."""

    def test_valid_espidf_file(self):
        """Test that a valid ESP-IDF file has no issues."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = [
            'menu "Network"\n',
            "    config NET_ENABLED\n",
            '        bool "Enable networking"\n',
            "        help\n",
            "            Enable network stack.\n",
            "endmenu\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 0, f"Expected no issues, got: {issues}"
        finally:
            temp_path.unlink()

    def test_uppercase_config_names(self):
        """Test enforcement of uppercase config names."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = [
            "config LowercaseConfig\n",
            '    bool "Test"\n',
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 1
            assert "must be uppercase" in issues[0].message
        finally:
            temp_path.unlink()

    def test_tabs_not_allowed(self):
        """Test that tabs are not allowed in ESP-IDF style."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\tbool "Test"\n',  # Tab not allowed
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any(
                "Use spaces for indentation" in issue.message for issue in issues
            )
        finally:
            temp_path.unlink()

    def test_indentation_multiple_of_4(self):
        """Test that indentation must be multiple of 4 spaces."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '  bool "Test"\n',  # 2 spaces, should be 4
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("multiple of 4" in issue.message for issue in issues)
        finally:
            temp_path.unlink()


class TestFormatter:
    """Test formatting functionality."""

    def test_format_tabs_to_tabs(self):
        """Test formatting with tab indentation."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        input_lines = [
            "config TEST\n",
            '  bool "Test"\n',  # Wrong: spaces
            "  help\n",
            "   Help text.\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)

            # Check that output uses tabs
            assert any("\t" in line for line in formatted), "Should contain tabs"

            # Check help text indentation (tab + 2 spaces)
            help_text_line = [line for line in formatted if "Help text" in line][0]
            assert help_text_line.startswith("\t  "), (
                "Help text should be tab + 2 spaces"
            )
        finally:
            temp_path.unlink()

    def test_format_fix_comment_spacing(self):
        """Test that formatter adds space after # in comments."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        input_lines = ["#Bad comment\n"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            assert formatted[0] == "# Bad comment\n"
        finally:
            temp_path.unlink()

    def test_format_remove_trailing_whitespace(self):
        """Test that formatter removes trailing whitespace."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        input_lines = ["config TEST  \n"]  # Trailing spaces

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            assert formatted[0] == "config TEST\n"
        finally:
            temp_path.unlink()

    def test_consolidate_empty_lines(self):
        """Test consolidating multiple empty lines."""
        config = LinterConfig.zephyr_preset()
        config.consolidate_empty_lines = True
        linter = KconfigLinter(config)

        input_lines = [
            "config TEST1\n",
            '\tbool "Test 1"\n',
            "\n",
            "\n",
            "\n",
            "config TEST2\n",
            '\tbool "Test 2"\n',
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)

            # Count consecutive empty lines
            empty_count = 0
            max_consecutive = 0
            for line in formatted:
                if line.strip() == "":
                    empty_count += 1
                    max_consecutive = max(max_consecutive, empty_count)
                else:
                    empty_count = 0

            assert max_consecutive <= 1, "Should have at most 1 consecutive empty line"
        finally:
            temp_path.unlink()

    def test_hierarchical_indenting(self):
        """Test hierarchical indentation for nested items."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        input_lines = [
            'menu "Network"\n',
            "config NET\n",
            'bool "Enable"\n',
            "help\n",
            "Help text.\n",
            "endmenu\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)

            # Check indentation levels
            assert formatted[0] == 'menu "Network"\n'
            assert formatted[1].startswith("    config NET")  # 4 spaces
            assert formatted[2].startswith("        bool")  # 8 spaces
            assert formatted[3].startswith("        help")  # 8 spaces
            assert formatted[4].startswith("            Help")  # 12 spaces
            assert formatted[5] == "endmenu\n"
        finally:
            temp_path.unlink()


class TestLineTypeDetection:
    """Test line type detection."""

    def test_detect_config(self):
        """Test detection of config keyword."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type("config TEST") == "config"
        assert linter._get_line_type("  config TEST") == "config"

    def test_detect_menuconfig(self):
        """Test detection of menuconfig keyword."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type("menuconfig TEST") == "menuconfig"

    def test_detect_help(self):
        """Test detection of help keyword."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type("help") == "help"
        assert linter._get_line_type("\thelp") == "help"

    def test_detect_bool(self):
        """Test detection of bool option."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type('\tbool "Test"') == "option"
        assert linter._get_line_type('\tint "Value"') == "option"
        assert linter._get_line_type('\tstring "Text"') == "option"

    def test_detect_depends(self):
        """Test detection of depends on."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type("\tdepends on FOO") == "option"

    def test_detect_comment(self):
        """Test detection of comments."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type("# Comment") == "comment_line"
        assert linter._get_line_type("  # Comment") == "comment_line"


class TestConfigNameValidation:
    """Test config name validation."""

    def test_config_name_length(self):
        """Test detection of overly long config names."""
        config = LinterConfig.zephyr_preset()
        config.max_option_name_length = 10
        linter = KconfigLinter(config)

        lines = [f"config {'A' * 20}\n"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("exceeds 10 characters" in issue.message for issue in issues)
        finally:
            temp_path.unlink()

    def test_prefix_length(self):
        """Test detection of short prefixes."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = ["config AB_TEST\n"]  # Prefix "AB" is only 2 chars

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("at least 3 characters" in issue.message for issue in issues)
        finally:
            temp_path.unlink()


class TestCustomConfiguration:
    """Test custom configuration options."""

    def test_use_spaces_option(self):
        """Test custom use_spaces option."""
        config = LinterConfig.zephyr_preset()
        config.use_spaces = True
        config.primary_indent_spaces = 2

        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\tbool "Test"\n',  # Tab when spaces required
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("Use spaces" in issue.message for issue in issues)
        finally:
            temp_path.unlink()

    def test_custom_line_length(self):
        """Test custom max line length."""
        config = LinterConfig.zephyr_preset()
        config.max_line_length = 50

        linter = KconfigLinter(config)

        lines = ["# " + "x" * 60 + "\n"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("exceeds 50 characters" in issue.message for issue in issues)
        finally:
            temp_path.unlink()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        issues = linter.lint_file(Path("/nonexistent/file.Kconfig"))
        assert len(issues) == 1
        assert "Failed to read file" in issues[0].message

    def test_format_file_not_found(self):
        """Test format handling of non-existent file."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        formatted, issues = linter.format_file(Path("/nonexistent/file.Kconfig"))
        assert len(formatted) == 0
        assert len(issues) == 1
        assert "Failed to read file" in issues[0].message

    def test_mixed_tabs_and_spaces(self):
        """Test detection of mixed tabs and spaces."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\t  bool "Test"\n',  # Tab + spaces mixed
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any("Mixed tabs and spaces" in issue.message for issue in issues)
        finally:
            temp_path.unlink()

    def test_empty_file(self):
        """Test handling of empty file."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 0
        finally:
            temp_path.unlink()

    def test_consolidate_empty_lines_linting(self):
        """Test linting with consolidate empty lines option."""
        config = LinterConfig.zephyr_preset()
        config.consolidate_empty_lines = True
        linter = KconfigLinter(config)

        lines = [
            "config TEST1\n",
            "\n",
            "\n",
            "\n",
            "config TEST2\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert any(
                "Multiple consecutive empty lines" in issue.message for issue in issues
            )
        finally:
            temp_path.unlink()

    def test_all_line_types(self):
        """Test detection of all line types."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        assert linter._get_line_type('menu "Test"') == "menu"
        assert linter._get_line_type("endmenu") == "endmenu"
        assert linter._get_line_type("choice") == "choice"
        assert linter._get_line_type("endchoice") == "endchoice"
        assert linter._get_line_type("if FOO") == "if"
        assert linter._get_line_type("endif") == "endif"
        assert linter._get_line_type('source "path"') == "source"
        assert linter._get_line_type('comment "test"') == "comment"
        assert linter._get_line_type('\ttristate "Test"') == "option"
        assert linter._get_line_type('\thex "Value"') == "option"
        assert linter._get_line_type("\tdef_bool y") == "option"
        assert linter._get_line_type("\tdef_tristate y") == "option"
        assert linter._get_line_type('\tprompt "Text"') == "option"
        assert linter._get_line_type("\tdefault y") == "option"
        assert linter._get_line_type("\tselect FOO") == "option"
        assert linter._get_line_type("\timply BAR") == "option"
        assert linter._get_line_type("\trange 0 100") == "option"
        assert linter._get_line_type('\toption env="VAR"') == "option"
        assert linter._get_line_type("some random text") == "other"

    def test_config_name_without_underscore(self):
        """Test config name validation without underscore."""
        config = LinterConfig.espidf_preset()
        linter = KconfigLinter(config)

        lines = ["config TESTING\n"]  # No underscore, no prefix warning

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            # Should not complain about prefix length
            assert not any("prefix" in issue.message.lower() for issue in issues)
        finally:
            temp_path.unlink()

    def test_invalid_config_line(self):
        """Test config line that doesn't match pattern."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        # _check_config_name should handle lines that don't match
        linter._check_config_name("config", 1)
        assert len(linter.issues) == 0  # Should not crash or add issues

    def test_comment_with_only_hash(self):
        """Test single # character without text."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = ["#\n"]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            # Should not complain about single #
            assert not any("space after #" in issue.message for issue in issues)
        finally:
            temp_path.unlink()

    def test_format_with_spaces_hierarchical(self):
        """Test formatting with spaces and hierarchical indenting."""
        config = LinterConfig.zephyr_preset()
        config.use_spaces = True
        config.indent_sub_items = True
        linter = KconfigLinter(config)

        input_lines = [
            'menu "Test"\n',
            "config FOO\n",
            'bool "Test"\n',
            "help\n",
            "Help text.\n",
            "endmenu\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            # Verify spaces are used
            assert all("\t" not in line for line in formatted if line.strip())
        finally:
            temp_path.unlink()

    def test_format_tabs_hierarchical(self):
        """Test formatting with tabs and hierarchical indenting."""
        config = LinterConfig.zephyr_preset()
        config.indent_sub_items = True
        linter = KconfigLinter(config)

        input_lines = [
            'menu "Test"\n',
            "config FOO\n",
            'bool "Test"\n',
            "endmenu\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            # Config should be indented with 1 tab (inside menu)
            assert formatted[1].startswith("\tconfig")
        finally:
            temp_path.unlink()

    def test_format_other_line_type(self):
        """Test formatting of 'other' line types."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        input_lines = [
            "config FOO\n",
            '  bool "Test"\n',
            "  some random text\n",  # 'other' type
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            # Other line should be indented like an option
            assert formatted[2].startswith("\tsome random text")
        finally:
            temp_path.unlink()

    def test_format_empty_line_not_consolidate(self):
        """Test formatting preserves multiple empty lines when not consolidating."""
        config = LinterConfig.zephyr_preset()
        config.consolidate_empty_lines = False
        linter = KconfigLinter(config)

        input_lines = [
            "config TEST1\n",
            "\n",
            "\n",
            "config TEST2\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(input_lines)
            temp_path = Path(f.name)

        try:
            formatted, _ = linter.format_file(temp_path)
            empty_count = sum(1 for line in formatted if line.strip() == "")
            assert empty_count == 2  # Both empty lines preserved
        finally:
            temp_path.unlink()

    def test_help_keyword_in_help_section(self):
        """Test that help keyword itself doesn't get checked as help text."""
        config = LinterConfig.zephyr_preset()
        linter = KconfigLinter(config)

        lines = [
            "config TEST\n",
            '\tbool "Test"\n',
            "\thelp\n",  # This is the help keyword
            "\t  Text.\n",
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.writelines(lines)
            temp_path = Path(f.name)

        try:
            issues = linter.lint_file(temp_path)
            assert len(issues) == 0
        finally:
            temp_path.unlink()

    def test_lint_issue_string_representation(self):
        """Test LintIssue string formatting."""
        from main import LintIssue

        issue_with_col = LintIssue(10, 5, "error", "Test message")
        assert str(issue_with_col) == "Line 10:5: [error] Test message"

        issue_no_col = LintIssue(10, None, "warning", "Test message")
        assert str(issue_no_col) == "Line 10: [warning] Test message"


class TestCLI:
    """Test command-line interface."""

    def test_cli_basic_lint(self):
        """Test basic CLI linting."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write('config TEST\n\tbool "Test"\n')
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", str(temp_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "0 issue(s)" in result.stdout
        finally:
            temp_path.unlink()

    def test_cli_with_issues(self):
        """Test CLI with files that have issues."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write("config TEST  \n")  # Trailing space
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", str(temp_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "Trailing whitespace" in result.stdout
        finally:
            temp_path.unlink()

    def test_cli_file_not_found(self):
        """Test CLI with non-existent file."""
        result = subprocess.run(
            [sys.executable, "main.py", "/nonexistent/file.Kconfig"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert "File not found" in result.stderr

    def test_cli_write_mode(self):
        """Test CLI in write/format mode."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write('#Bad comment\nconfig TEST\n  bool "Test"\n')
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", "--write", str(temp_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "Formatted 1 file(s)" in result.stdout

            # Verify file was actually formatted
            with open(temp_path) as f:
                content = f.read()
                assert content.startswith("# Bad comment")
                assert "\t" in content  # Should have tabs
        finally:
            temp_path.unlink()

    def test_cli_espidf_preset(self):
        """Test CLI with ESP-IDF preset."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write('config lowercase\n    bool "Test"\n')
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", "--preset", "espidf", str(temp_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "uppercase" in result.stdout
        finally:
            temp_path.unlink()

    def test_cli_custom_options(self):
        """Test CLI with custom options."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write("# " + "x" * 60 + "\n")
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--max-line-length",
                    "50",
                    str(temp_path),
                ],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 1
            assert "exceeds 50 characters" in result.stdout
        finally:
            temp_path.unlink()

    def test_cli_verbose(self):
        """Test CLI with verbose output."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write('config TEST\n\tbool "Test"\n')
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", "--verbose", str(temp_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert "Linting" in result.stdout
        finally:
            temp_path.unlink()

    def test_cli_multiple_files(self):
        """Test CLI with multiple files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f1:
            f1.write('config TEST1\n\tbool "Test"\n')
            temp_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f2:
            f2.write('config TEST2\n\tbool "Test"\n')
            temp_path2 = Path(f2.name)

        try:
            result = subprocess.run(
                [sys.executable, "main.py", str(temp_path1), str(temp_path2)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
        finally:
            temp_path1.unlink()
            temp_path2.unlink()

    def test_cli_all_options(self):
        """Test CLI with all available options."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".Kconfig", delete=False
        ) as f:
            f.write('config TEST\nbool "Test"\n')
            temp_path = Path(f.name)

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--use-spaces",
                    "--primary-indent",
                    "2",
                    "--help-indent",
                    "4",
                    "--max-line-length",
                    "120",
                    "--max-option-length",
                    "40",
                    "--uppercase-configs",
                    "--min-prefix-length",
                    "2",
                    "--indent-sub-items",
                    "--consolidate-empty-lines",
                    "--write",
                    "--verbose",
                    str(temp_path),
                ],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )
            assert "Formatted" in result.stdout
        finally:
            temp_path.unlink()
