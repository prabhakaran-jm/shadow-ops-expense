from nova_act import NovaAct, Workflow

with Workflow(
    workflow_definition_name="shadow-ops-test",
    model_id="nova-act-latest"
) as wf:
    with NovaAct(
        starting_page="https://example.com",
        workflow=wf,
    ) as nova:
        result = nova.act("Click on the 'More information' link")
        print(f"Success: {result.success}")
        print(f"Response: {result.response}")
