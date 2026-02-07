"""State management for admin UI."""

STATE_JS = """const state = {
  tokens: [],
  projects: [],
  users: [],
  deletionRequests: [],
  selectedTokenId: null,
  view: 'tokens',
  tokenRequests: [],
  logs: {
    projectId: null,
    events: [],
    lastBefore: null,
    hasMore: false,
    loading: false,
    selectedEventId: null,
    selectedEventJson: '',
  },
};"""
