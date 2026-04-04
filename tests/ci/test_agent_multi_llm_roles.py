"""Tests for planner / navigator / extractor LLM resolution on Agent."""

import pytest
from conftest import create_mock_llm

from browser_use.agent.service import Agent


def test_multi_llm_single_llm_defaults_planner_navigator_extractor(mock_llm):
	agent = Agent(task='task', llm=mock_llm)
	assert agent.planner_llm is mock_llm
	assert agent.llm is mock_llm
	assert agent.settings.navigator_llm is mock_llm
	assert agent.settings.page_extraction_llm is mock_llm
	assert agent.judge_llm is mock_llm


def test_navigator_override_uses_planner_for_extractor_and_judge():
	planner = create_mock_llm()
	planner.model = 'planner-model'
	navigator = create_mock_llm()
	navigator.model = 'navigator-model'
	agent = Agent(task='task', llm=planner, navigator_llm=navigator)
	assert agent.planner_llm is planner
	assert agent.llm is navigator
	assert agent.settings.page_extraction_llm is planner
	assert agent.judge_llm is planner


def test_page_extraction_override():
	planner = create_mock_llm()
	extractor = create_mock_llm()
	extractor.model = 'extract-only'
	agent = Agent(task='task', llm=planner, page_extraction_llm=extractor)
	assert agent.planner_llm is planner
	assert agent.llm is planner
	assert agent.settings.page_extraction_llm is extractor


def test_extractor_llm_alias_matches_page_extraction_llm():
	planner = create_mock_llm()
	extractor = create_mock_llm()
	agent = Agent(task='task', llm=planner, extractor_llm=extractor)
	assert agent.settings.page_extraction_llm is extractor


def test_page_extraction_llm_and_extractor_llm_same_instance_ok():
	planner = create_mock_llm()
	ext = create_mock_llm()
	Agent(task='task', llm=planner, page_extraction_llm=ext, extractor_llm=ext)


def test_page_extraction_llm_extractor_llm_conflict_raises():
	planner = create_mock_llm()
	e1 = create_mock_llm()
	e2 = create_mock_llm()
	with pytest.raises(ValueError, match='page_extraction_llm and extractor_llm'):
		Agent(task='task', llm=planner, page_extraction_llm=e1, extractor_llm=e2)
