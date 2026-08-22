def find_compatible_workflow(page, workflows):

    # ========================================================
    # TEMPORARY SELF-HEALING TEST
    # ========================================================
    # Force the test workflow to be selected.
    # REMOVE THIS BLOCK AFTER TESTING.
    # ========================================================

    


    # ========================================================
    # NORMAL MEMORY MATCHING
    # ========================================================

    for workflow in reversed(workflows):

        compatible = True

        for action in workflow.get("actions", []):

            if action.get("tool") == "click":

                value = action.get(
                    "value",
                    ""
                )

                count = page.get_by_text(
                    value,
                    exact=True
                ).count()

                if count == 0:

                    compatible = False

                    break

        if compatible:

            return workflow

    return None