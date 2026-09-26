echo "Remove legacy temporary passwordless sudo grants"

# Migration queues are per-user; the privileged repair is once per machine.
if ! "$OMARCHY_PATH/bin/omarchy-sudo-passwordless" __migration-complete; then
  sudo "$OMARCHY_PATH/bin/omarchy-sudo-passwordless" __migrate
fi
