# Claude Code 共通リポジトリ管理
CLAUDE_SHARED_REPO   ?= https://github.com/k-negishi/claude-python-toolkit.git
CLAUDE_SHARED_BRANCH ?= main
CLAUDE_SHARED_PREFIX  = .claude-shared
CLAUDE_DIR            = .claude

.PHONY: claude-init claude-update claude-push claude-link claude-clean claude-status

# 初回セットアップ: Subtree追加 + symlink作成
claude-init:
	@echo "Adding claude-python-toolkit as subtree..."
	git subtree add --prefix=$(CLAUDE_SHARED_PREFIX) $(CLAUDE_SHARED_REPO) $(CLAUDE_SHARED_BRANCH) --squash
	@$(MAKE) claude-link

# 共通リポジトリから更新を取得 + symlink再作成
claude-update:
	@echo "Pulling updates from claude-python-toolkit..."
	git subtree pull --prefix=$(CLAUDE_SHARED_PREFIX) $(CLAUDE_SHARED_REPO) $(CLAUDE_SHARED_BRANCH) --squash
	@$(MAKE) claude-link

# ローカルの変更を共通リポジトリにプッシュ
claude-push:
	@echo "Pushing changes to claude-python-toolkit..."
	git subtree push --prefix=$(CLAUDE_SHARED_PREFIX) $(CLAUDE_SHARED_REPO) $(CLAUDE_SHARED_BRANCH)

# symlink を作成（既存の実ファイルは保持）
claude-link:
	@echo "Creating symlinks from .claude-shared/ to .claude/..."
	@mkdir -p $(CLAUDE_DIR)/commands $(CLAUDE_DIR)/skills $(CLAUDE_DIR)/agents
	@# commands/
	@find $(CLAUDE_SHARED_PREFIX)/commands -maxdepth 1 -type f | while read file; do \
		base=$$(basename "$$file"); \
		target="$(CLAUDE_DIR)/commands/$$base"; \
		if [ ! -e "$$target" ]; then \
			ln -sf "../../../.claude-shared/commands/$$base" "$$target"; \
			echo "  Link: $$target -> .claude-shared/commands/$$base"; \
		else \
			echo "  Skip (exists): $$target"; \
		fi; \
	done
	@# skills/
	@find $(CLAUDE_SHARED_PREFIX)/skills -maxdepth 1 -type d ! -path $(CLAUDE_SHARED_PREFIX)/skills | while read dir; do \
		base=$$(basename "$$dir"); \
		target="$(CLAUDE_DIR)/skills/$$base"; \
		if [ ! -e "$$target" ]; then \
			ln -sf "../../../.claude-shared/skills/$$base" "$$target"; \
			echo "  Link: $$target -> .claude-shared/skills/$$base"; \
		else \
			echo "  Skip (exists): $$target"; \
		fi; \
	done
	@# agents/
	@find $(CLAUDE_SHARED_PREFIX)/agents -maxdepth 1 -type f | while read file; do \
		base=$$(basename "$$file"); \
		target="$(CLAUDE_DIR)/agents/$$base"; \
		if [ ! -e "$$target" ]; then \
			ln -sf "../../../.claude-shared/agents/$$base" "$$target"; \
			echo "  Link: $$target -> .claude-shared/agents/$$base"; \
		else \
			echo "  Skip (exists): $$target"; \
		fi; \
	done

# symlink を削除（実ファイルは保持）
claude-clean:
	@echo "Removing symlinks in .claude/..."
	@find $(CLAUDE_DIR) -type l -delete
	@echo "Symlinks removed. Run 'make claude-link' to recreate."

# Subtree の状態確認
claude-status:
	@echo "Subtree status:"
	@echo "  Prefix: $(CLAUDE_SHARED_PREFIX)"
	@echo "  Remote: $(CLAUDE_SHARED_REPO)"
	@echo "  Branch: $(CLAUDE_SHARED_BRANCH)"
	@echo ""
	@echo "Recent subtree commits:"
	@git log --grep="git-subtree-dir: $(CLAUDE_SHARED_PREFIX)" --oneline -5 || echo "  No subtree commits found yet"
