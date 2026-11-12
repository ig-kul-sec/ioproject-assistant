from ioassistant import leadership, report, resources


def _kinds(links):
    return sorted(x["kind"] for x in links)


def test_config_is_valid():
    entries = resources.load()
    assert [e["name"] for e in entries] == ["Network 2.0", "EoL OS management", "OS Lifecycle management"]
    for entry in entries:
        for link in resources.find(entry["match"][0]):  # builds every link: raises on an unknown kind
            assert link["url"].startswith("https://") and '"' not in link["url"] and " " not in link["url"]
            if link["kind"] in ("epic", "initiative"):
                assert link["key"] and link["label"] == link["key"] and link["url"].endswith(link["key"])


def test_find_matches_whole_words_only():
    net = resources.find("Network 2.0")
    assert _kinds(net) == ["chat", "confluence", "epic", "planner"]
    assert resources.of_kind(net, "epic")[0]["key"] == "IOSP-477"
    # EoL and Debian OS lifecycle are separate projects with their own resources
    eol = resources.find("End of life (EoL) servers and OS upgrades")
    assert _kinds(eol) == ["chat", "chat", "chat", "confluence", "initiative", "sharepoint"]
    assert resources.of_kind(eol, "sharepoint")[0]["label"] == "Upgrading Gentoo to Debian folder"
    assert resources.of_kind(eol, "initiative")[0]["key"] == "SI-5" and resources.of_kind(eol, "confluence")[0]["label"] == "EoL OS management"
    deb = resources.find("Debian OS lifecycle management")
    assert _kinds(deb) == ["confluence", "epic", "planner"]
    assert resources.of_kind(deb, "epic")[0]["key"] == "IOSP-806" and resources.of_kind(deb, "confluence")[0]["label"] == "OS Lifecycle management"
    for name in ("EOL upgrades (ABS servers)", "End-of-life (EOL) upgrades", "Migration EOL/EOS OSs"):
        assert resources.find(name) == eol, name
    assert resources.find("OS lifecycle management") == deb and resources.find("Network v2.0")
    for name in ("Rubrik DR backup", "Video streams", "Oracle RAC", "", None):  # "eos" inside "Videos" must not match
        assert resources.find(name) == [], name


def test_status_report_adds_the_fixed_resources():
    data = {"projects": [
        {"name": "Network 2.0", "tickets": [{"key": "IOSP-477", "name": "Network v2", "status": "In Progress", "epic": True}],
         "links": {"confluence": [{"label": "Run page", "url": "https://wiki.example/run"}]}},
        {"name": "End of life (EoL) servers and OS upgrades"},
        {"name": "Debian OS lifecycle management"},
        {"name": "Rubrik DR backup"},
    ]}
    html = report.render(data, "IOProjectAssistantReport_20261109_0900")
    cards = html.split("Project sources</summary>")[1:]
    net, eol, deb, rubrik = (c[:c.index("Jira tickets for this project (active)")] for c in cards)
    assert net.count(">IOSP-477</a>") == 1 and "Network v2" in net  # the run's own epic row (with its name) wins, no duplicate
    assert "Run page" in net and ">Network v2.0</a>" in net and "Network 2.0 project chat" in net
    assert ">Planner<" in net and "Network 2.0 Planner" in net and "Jira strategic initiative" not in net
    assert ">SI-5</a>" in eol and "Jira strategic initiative" in eol and "EoL OS management project chat" in eol
    assert "Upgrading Gentoo to Debian folder" in eol  # the fixed SharePoint folder of the EoL project
    assert "IOSP-806" not in eol and ">Planner<" not in eol and "OS Lifecycle management" not in eol
    assert "IOSP-806" in deb and "OS Lifecycle management</a>" in deb and ">Planner<" in deb and "OS Lifecycle management Planner" in deb
    assert "SI-5" not in deb and "Jira strategic initiative" not in deb and "project chat" not in deb and "EoL OS management" not in deb
    assert "Planner" not in rubrik and "Jira strategic initiative" not in rubrik and "planner.cloud" not in rubrik


def test_eol_drops_links_of_the_debian_project():
    wiki = "https://sectigo.atlassian.net/wiki/spaces/CO/pages/"
    found = {
        "sharepoint": [{"label": "Upgrading Gentoo to Debian folder", "url": "https://comodoca.sharepoint.com/sites/IOProjectTeam/Shared Documents/Upgrading Gentoo to Debian"},
                       {"label": "Deck", "url": "https://comodoca.sharepoint.com/sites/IOProjectTeam/Shared Documents/Presentations/Deck.pptx"}],
        "confluence": [{"label": "OS lifecycle mngmnt roadmap", "url": wiki + "94177517/OS+lifecycle+mngmnt+roadmap"},
                       {"label": "OS Lifecycle management", "url": wiki + "94178822/OS+Lifecycle+management"},
                       {"label": "Run page", "url": "https://wiki.example/run"}],
    }
    tickets = [{"key": "IOSP-806", "name": "Debian epic", "status": "In Progress", "epic": True},
               {"key": "COR-11842", "name": "Debian P0", "status": "In Progress", "epic": True}]
    html = report.render({"projects": [{"name": "End of life (EoL) servers and OS upgrades", "links": found, "tickets": tickets},
                                       {"name": "Debian OS lifecycle management", "links": found, "tickets": tickets}]},
                         "IOProjectAssistantReport_20261109_0900")
    eol, deb = (c[:c.index("Jira tickets for this project (active)")] for c in html.split("Project sources</summary>")[1:])
    # the Gentoo to Debian folder is a fixed EoL source: shown once (the run-found copy of the same folder is not repeated)
    assert eol.count("Upgrading Gentoo to Debian") == 1 and "94177517" not in eol and "94178822" not in eol and "IOSP-806" not in eol
    assert "Deck" in eol and "Run page" in eol and ">COR-11842</a>" in eol  # the other links stay
    assert "Gentoo" in deb and "94177517" in deb and "IOSP-806" in deb  # only EoL is filtered
    share = "https://comodoca.sharepoint.com/:f:/r/sites/IOProjectTeam/Shared%20Documents/Upgrading%20Gentoo%20to%20Debian?d=x&csf=1"
    assert resources.drop_excluded([{"url": share}], "EOL upgrades") != []  # no longer excluded from EoL
    assert resources.drop_excluded([{"url": share}], "Debian OS lifecycle management") != []
    fixed = resources.of_kind(resources.find("EOL upgrades"), "sharepoint")
    assert resources.drop_known([{"url": share}], fixed) == []  # same folder, other sharing link
    other = share.replace("Upgrading%20Gentoo%20to%20Debian", "Other%20folder")
    assert resources.drop_known([{"url": other}], fixed) != []  # another folder stays

    lead = leadership.render({"projects": [{"name": "End of life (EoL) servers and OS upgrades", "resources": {
        "epics": [{"key": "IOSP-806", "url": "https://sectigo.atlassian.net/browse/IOSP-806"}],
        "confluence": found["confluence"], "sharepoint": found["sharepoint"]}}]}, "IOProjectLeadershipUpdates_20261109_0900")
    key = lead.split("Key project resources")[1]
    assert "IOSP-806" not in key and "94177517" not in key and key.count("Upgrading Gentoo to Debian") == 1 and "Run page" in key and "Deck" in key


def test_leadership_report_adds_the_fixed_resources():
    data = {"projects": [{"name": "Network v2.0"}, {"name": "Rubrik"}]}
    html = leadership.render(data, "IOProjectLeadershipUpdates_20261109_0900")
    net, rubrik = html.split("Key project resources")[1:3]
    assert "IOSP-477" in net and "Network 2.0 project chat" in net and "Network 2.0 Planner" in net
    assert ">Planner<" in net and "Jira strategic initiative" not in net
    assert "planner.cloud" not in rubrik and "IOSP-477" not in rubrik
