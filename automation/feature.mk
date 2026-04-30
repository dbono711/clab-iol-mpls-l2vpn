CLAB ?= clab-iol-mpls-l2vpn
LOG_FILE ?= setup.log
REPO_ROOT := ../..
VENV_DIR ?= $(REPO_ROOT)/.venv
REQ_FILE ?= $(REPO_ROOT)/requirements.txt
ANSIBLE_HOSTS ?= $(REPO_ROOT)/clab-iol-mpls-l2vpn/ansible-inventory.yml
ANSIBLE_CONFIG ?= $(REPO_ROOT)/automation/ansible.cfg
ANSIBLE_PLAYBOOK ?= $(REPO_ROOT)/automation/playbooks/configure.yml
GROUP_VARS_DIR ?= $(REPO_ROOT)/automation/group_vars
TOPOLOGY_FILE ?= $(REPO_ROOT)/setup.yml
FEATURE_DIR ?= .
FEATURE_DIR_ABS := $(abspath $(FEATURE_DIR))
FEATURE_HOST_VARS_DIR ?= $(FEATURE_DIR_ABS)/host_vars
FEATURE_TEMPLATES_DIR ?= $(FEATURE_DIR_ABS)/templates

define log
	echo "[$(shell date '+%Y-%m-%d %H:%M:%S')] $1" >> $(LOG_FILE)
endef

define exec_shell
	docker exec -it $(CLAB)-$1 bash
endef

define exec_ssh
	ssh admin@$(CLAB)-$1
endef

define run_ansible
	ANSIBLE_CONFIG=$(ANSIBLE_CONFIG) \
	$(VENV_DIR)/bin/ansible-playbook \
		-i $(ANSIBLE_HOSTS) \
		$(ANSIBLE_PLAYBOOK) \
		-e feature_dir=$(FEATURE_DIR_ABS) \
		-e feature_host_vars_dir=$(FEATURE_HOST_VARS_DIR) \
		-e feature_templates_dir=$(FEATURE_TEMPLATES_DIR)
endef

.PHONY: initialize-log
initialize-log:
	@echo -n "" > $(LOG_FILE)

.PHONY: initialize-virtual-environment
initialize-virtual-environment: initialize-log
	@if [ ! -d $(VENV_DIR) ]; then \
		$(call log,Creating virtual environment...); \
		python3 -m venv $(VENV_DIR) >> $(LOG_FILE) 2>&1; \
		$(call log,Installing requirements in virtual environment...); \
		$(VENV_DIR)/bin/pip install -r $(REQ_FILE) >> $(LOG_FILE) 2>&1; \
	else \
		$(call log,Virtual environment already exists.); \
	fi

.PHONY: lab
lab: initialize-virtual-environment
	@$(call log,Deploying ContainerLAB topology...)
	@sudo clab deploy --topo $(TOPOLOGY_FILE) >> $(LOG_FILE) 2>&1
	@sleep 5
	@$(call log,ContainerLAB topology successfully deployed.)

.PHONY: configure
configure: lab
	@$(call log,Starting configuration...)
	@$(call log,Running ansible playbook for iol configuration...)
	@$(call run_ansible) >> $(LOG_FILE) 2>&1
	@echo "Configuration complete. Check '$(LOG_FILE)' for detailed output."

.PHONY: all
all: configure

.PHONY: configure-only
configure-only: initialize-virtual-environment
	@$(call log,Starting configuration...)
	@$(call log,Running ansible playbook for iol configuration...)
	@$(call run_ansible) >> $(LOG_FILE) 2>&1
	@echo "Configuration complete. Check '$(LOG_FILE)' for detailed output."

.PHONY: clean
clean: initialize-log
	@$(call log,Cleaning up...)
	@sudo clab destroy --cleanup --topo $(TOPOLOGY_FILE) >> $(LOG_FILE) 2>&1
	@rm -rf $(VENV_DIR) >> $(LOG_FILE) 2>&1
	@$(call log,Cleaning complete.)
	@echo "Cleaning complete. Check '$(LOG_FILE)' for detailed output."

.PHONY: west1 core1 east1
west1 core1 east1:
	$(call exec_ssh,$(subst -,_,$@))

.PHONY: client1 client2
client1 client2:
	$(call exec_shell,$(subst -,_,$@))
