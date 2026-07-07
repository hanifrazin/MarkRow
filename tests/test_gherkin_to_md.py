import pytest
from pathlib import Path
import tempfile
import os

from src.core.models import GherkinFeature, GherkinScenario, GherkinStep, GherkinBackground
from src.core.parsers.gherkin_parser import GherkinParser, parse_text as parse_gherkin_text
from src.core.parsers.md_parser import parse_text as parse_md_text
from src.core.writers.gherkin_writer import GherkinWriter
from src.core.writers.md_writer import MarkdownWriter


SAMPLE_FEATURE = """@smoke @regression
Feature: Login
  As a user I want to login so that I can access the application

  Background:
    Given I am on the login page

  @positive
  Scenario: Successful login with valid credentials
    Given I enter username "admin"
    And I enter password "admin123"
    When I click the login button
    Then I should see the dashboard
    And I should see the welcome message

  @negative
  Scenario Outline: Login with invalid credentials
    Given I enter username "<username>"
    And I enter password "<password>"
    When I click the login button
    Then I should see an error message

    Examples:
      | username | password   |
      | invalid  | wrongpass  |
      | admin    | wrongpass  |
"""


SAMPLE_MARKDOWN = """# Module: Login

**Tags**: @smoke @regression
**Description**: As a user I want to login so that I can access the application

**Background**:
1. I am on the login page

## Scenario: Successful login with valid credentials

**Tags**: @positive
**Precondition**:
1. I enter username "admin"
2. I enter password "admin123"

**Test Steps**:
1. I click the login button

**Expected Result**:
1. I should see the dashboard
2. I should see the welcome message

## Scenario: Login with invalid credentials

**Tags**: @negative
**Precondition**:
1. I enter username "<username>"
2. I enter password "<password>"

**Test Steps**:
1. I click the login button

**Expected Result**:
1. I should see an error message

**Test Data**:
| username | password |
| invalid | wrongpass |
| admin | wrongpass |
"""


class TestGherkinParser:
    def test_parse_feature(self):
        feature = parse_gherkin_text(SAMPLE_FEATURE)
        assert feature.name == "Login"
        assert feature.tags == ["@smoke", "@regression"]
        assert "As a user I want to login" in feature.description
        assert len(feature.background.steps) == 1
        assert feature.background.steps[0].keyword == "Given"
        assert feature.background.steps[0].text == "I am on the login page"

    def test_parse_scenarios(self):
        feature = parse_gherkin_text(SAMPLE_FEATURE)
        assert len(feature.scenarios) == 2

        s1 = feature.scenarios[0]
        assert s1.name == "Successful login with valid credentials"
        assert s1.tags == ["@positive"]
        assert len(s1.steps) == 5

        s2 = feature.scenarios[1]
        assert s2.name == "Login with invalid credentials"
        assert s2.tags == ["@negative"]
        assert len(s2.examples) == 2
        assert s2.examples[0]["username"] == "invalid"
        assert s2.examples[1]["password"] == "wrongpass"

    def test_parse_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.feature', delete=False, encoding='utf-8') as f:
            f.write(SAMPLE_FEATURE)
            tmp_path = f.name
        try:
            parser = GherkinParser(tmp_path)
            feature = parser.parse()
            assert feature.name == "Login"
            assert len(feature.scenarios) == 2
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestGherkinWriter:
    def test_write_feature(self):
        feature = GherkinFeature(
            name="Login",
            tags=["@smoke"],
            description="Simple login feature",
            background=GherkinBackground(steps=[GherkinStep(keyword="Given", text="I am on the page")]),
            scenarios=[
                GherkinScenario(
                    name="Valid login",
                    tags=["@positive"],
                    steps=[
                        GherkinStep(keyword="Given", text="I enter valid credentials"),
                        GherkinStep(keyword="When", text="I click login"),
                        GherkinStep(keyword="Then", text="I see dashboard"),
                    ],
                )
            ],
        )
        output = GherkinWriter.render(feature)
        assert "Feature: Login" in output
        assert "@smoke" in output
        assert "Scenario: Valid login" in output
        assert "Background:" in output
        assert "Given I am on the page" in output
        assert "When I click login" in output

    def test_write_scenario_outline(self):
        feature = GherkinFeature(
            name="Data driven login",
            scenarios=[
                GherkinScenario(
                    name="Login with multiple users",
                    steps=[GherkinStep(keyword="Given", text="I login as <user>")],
                    examples=[{"user": "admin"}, {"user": "guest"}],
                )
            ],
        )
        output = GherkinWriter.render(feature)
        assert "Scenario Outline: Login with multiple users" in output
        assert "Examples:" in output
        assert "| user |" in output


class TestMarkdownWriter:
    def test_render_feature_to_md(self):
        feature = GherkinFeature(
            name="Login",
            tags=["@smoke"],
            description="Login feature",
            scenarios=[
                GherkinScenario(
                    name="Valid login",
                    tags=["@positive"],
                    steps=[
                        GherkinStep(keyword="Given", text="I am on login page"),
                        GherkinStep(keyword="When", text="I enter credentials"),
                        GherkinStep(keyword="Then", text="I see dashboard"),
                    ],
                )
            ],
        )
        output = MarkdownWriter.render(feature)
        assert "# Module: Login" in output
        assert "## Scenario: Valid login" in output
        assert "**Tags**: @smoke" in output
        assert "**Precondition**:" in output
        assert "**Test Steps**:" in output
        assert "**Expected Result**:" in output

    def test_render_background(self):
        feature = GherkinFeature(
            name="Test",
            background=GherkinBackground(steps=[GherkinStep(keyword="Given", text="I am ready")]),
            scenarios=[
                GherkinScenario(
                    name="First scenario",
                    steps=[
                        GherkinStep(keyword="Given", text="Specific setup"),
                        GherkinStep(keyword="When", text="Do action"),
                        GherkinStep(keyword="Then", text="Check result"),
                    ],
                )
            ],
        )
        output = MarkdownWriter.render(feature)
        assert "**Background**:" in output
        assert "I am ready" in output


class TestRoundTrip:
    def test_gherkin_to_md_to_gherkin(self):
        feature = parse_gherkin_text(SAMPLE_FEATURE)
        md_output = MarkdownWriter.render(feature)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(md_output)
            md_path = f.name
        try:
            parsed_back = parse_md_text(md_output)
            gherkin_back = GherkinWriter.render(parsed_back)

            assert parsed_back.name == "Login"
            assert len(parsed_back.scenarios) == len(feature.scenarios)
            for orig, back in zip(feature.scenarios, parsed_back.scenarios):
                assert orig.name == back.name
                if orig.examples:
                    assert len(back.examples) == len(orig.examples)
        finally:
            Path(md_path).unlink(missing_ok=True)

    def test_md_to_gherkin_to_md(self):
        md_feature = parse_md_text(SAMPLE_MARKDOWN)
        gherkin_output = GherkinWriter.render(md_feature)

        parsed_back = parse_gherkin_text(gherkin_output)
        md_back = MarkdownWriter.render(parsed_back)

        assert parsed_back.name == "Login"
        assert len(parsed_back.scenarios) == 2
        assert md_back
        assert "# Module: Login" in md_back


class TestTagClassifier:
    def test_classify_tags(self):
        from src.core.utils.tag_classifier import classify_tag, classify_tags
        assert classify_tag("@smoke") == "smoke"
        assert classify_tag("@regression") == "regression"
        assert classify_tag("@p1") == "priority"
        assert classify_tag("@unknown") == "uncategorized"

        result = classify_tags(["@smoke", "@p2", "@custom"])
        assert "smoke" in result
        assert "priority" in result
        assert "uncategorized" in result


class TestConfigLoader:
    def test_migration_adds_new_fields(self):
        from src.core.utils.config_loader import _migrate_old_to_new, _is_old_format
        old_data = {"default_input_dir": "input", "default_output_dir": "output", "columns": []}
        assert _is_old_format(old_data)
        migrated = _migrate_old_to_new(old_data)
        assert "global" in migrated
        assert "excel" in migrated
        assert "gherkin" in migrated
        assert migrated["global"]["default_input_dir"] == "input"
        assert migrated["gherkin"]["default_tags"] == ["@mamow"]


class TestEdgeCases:
    def test_empty_feature(self):
        from src.core.parsers.gherkin_parser import GherkinParseError
        with pytest.raises(GherkinParseError):
            parse_gherkin_text("Just some random text\nNot a feature file")

    def test_feature_without_scenarios(self):
        feature = parse_gherkin_text("Feature: Empty\n  Just a description")
        assert feature.name == "Empty"
        assert len(feature.scenarios) == 0

    def test_scenario_without_steps(self):
        feature = parse_gherkin_text("Feature: Bare\n  Scenario: No steps")
        assert len(feature.scenarios) == 1
        assert len(feature.scenarios[0].steps) == 0

    def test_no_background_steps(self):
        feature = parse_gherkin_text("Feature: X\n  Scenario: S\n    Given a step")
        assert len(feature.background.steps) == 0

    def test_comments_ignored(self):
        feature = parse_gherkin_text("Feature: C\n  # this is a comment\n  Scenario: S\n    Given step")
        assert feature.name == "C"
        assert len(feature.scenarios) == 1

    def test_markdown_roundtrip_preserves_scenario_count(self):
        for i in range(3):
            feature = GherkinFeature(
                name=f"Test{i}",
                scenarios=[
                    GherkinScenario(name=f"S{j}", steps=[
                        GherkinStep(keyword="Given", text="setup"),
                        GherkinStep(keyword="When", text="action"),
                        GherkinStep(keyword="Then", text="verify"),
                    ]) for j in range(i + 1)
                ],
            )
            md = MarkdownWriter.render(feature)
            parsed = parse_md_text(md)
            assert len(parsed.scenarios) == i + 1, f"Expected {i+1} scenarios, got {len(parsed.scenarios)}"
