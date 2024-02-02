#!/usr/bin/env python3

import sys
from os import path, listdir
import yaml
if (sys.version_info.minor < 8,):
    from typing_extensions import Final
    from typing import Tuple
else:
    from typing import Final, Tuple

import click

def __generate_asciidoc(items: dict, config: dict) -> str:
    "Generate acsciidoc from items"

    close_table: Final = "|===\n\n"

    # Write key table
    output = """= Key

[cols="1,3", options=header]
|===
|Value
|Description
"""

    for status in config['statuses'].values():
        output += f"""
|
{{set:cellbgcolor:{status['color']}}}
{status['text']}
|
{{set:cellbgcolor!}}
{status['description']}
"""

    output += close_table

    # Write summary table
    output += "= Summary\n\n"
    output += __generate_table_header()

    for category in config['categories'].keys():
        if category not in items:
            continue
        for item in items[category]:
            output += __generate_summary_row(item, config)

    output += close_table

    # Write detail sections
    for category in config['categories'].keys():
        if category not in items:
            continue

        output += f"""<<<

# {config['categories'][category]['text']}

"""
        output += __generate_table_header()

        for item in items[category]:
            output += __generate_summary_row(item, config)

        output += close_table

        # Page break between table and descriptions looks nice
        output += "<<<\n\n"

        # Generate detailed sections
        for item in items[category]:
            output += __generate_detail(item, config)

    # Write final invisible table
    # This resets the bgcolor for future tables
    output += """
// Reset bgcolor for future tables
[grid=none,frame=none]
|===
|{set:cellbgcolor!}
|===
"""

    return output

def __generate_table_header() -> str:
    "Generate a standard asciidoc table header for item table"

    return """
[cols="1,2,2,3", options=header]
|===
|*Category*
|*Item Evaluated*
|*Observed Result*
|*Recommendation*

"""


def __will_item_generate_detail(item: dict, config: dict) -> bool:
    "Determine if an item file will cause a detail section to be generated."

    # Right now there is no difference between v0 and v1
    # if item['version'] == 'v0':
    #     return __will_item_generate_detail_v0(item, config)
    # if item['version'] == 'v1':
    #     return __will_item_generate_detail_v1(item, config)    


    # Only create section if not recommendation is not a skippable one
    # (defined in config) -OR- if additional_comments_text is defined.

    if (item['results']['additional_comments_text'] != "" or
        item['results']['recommendation'] not in config['skip_statuses']):
        return True
    else:
        return False


def __generate_detail(item: dict, config: dict) -> str:
    "Generate an AsciiDoc detail section"

    if item['version'] == 'v0':
        return __generate_detail_v0(item, config)
    if item['version'] == 'v1':
        return __generate_detail_v1(item, config)

def __generate_detail_v0 (item: dict, config: dict) -> str:
    "Generate an AsciiDoc detail section for a v0 item file"

    output: str = ""
    results: dict = item['results']
    metadata: dict = item['metadata']

    if __will_item_generate_detail(item, config):

        # Write descriptions
        output += f"""## {item['metadata']['item_evaluated']}

[cols=\"^\"]
|===
|
{{set:cellbgcolor:{config['statuses'][results['recommendation']]['color']}}}
{config['statuses'][results['recommendation']]['text']}
|===

*Observed Result*

{item['results']['result_text']}

"""

        if ('acceptance_criteria' in metadata and
            results['recommendation'] in metadata['acceptance_criteria']):
            output += """*Matching Status(es)*

"""

            for matching_status in metadata['acceptance_criteria'][results['recommendation']]:
                output += f"* {matching_status}\n"
            output += "\n"

        if results['recommendation'] not in config['skip_statuses']:
            if results['impact_risk_text'] != "":
                output += f"""*Impact and Risk*

{results['impact_risk_text']}

"""

            if results['remediation_text'] != "":
                output += f"""*Remediation Advise*

{results['remediation_text']}

"""

        if results['additional_comments_text'] != "":
            output += f"""*Additional Comments*

{results['additional_comments_text']}

"""

        if len(metadata['references']) > 0:
            output += """*Reference Link(s)*

"""
            for ref in metadata['references']:
                output += f"* {ref['url']}[{ref['title']}]\n"

            output += "\n"

    return output

def __generate_detail_v1 (item: dict, config: dict) -> str:
    "Generate an AsciiDoc detail section for a v0 item file"
    
    output: str = ""
    results: dict = item['results']
    metadata: dict = item['metadata']

    if __will_item_generate_detail(item, config):

        # Write descriptions
        output += f"""## {item['metadata']['item_evaluated']}

[cols=\"^\"]
|===
|
{{set:cellbgcolor:{config['statuses'][results['recommendation']]['color']}}}
{config['statuses'][results['recommendation']]['text']}
|===

*Observed Result*
"""
        if 'result_long_text' in results:
            output += f"""

{item['results']['result_long_text']}

"""
        else:
            output += f"""

{item['results']['result_short_text']}

"""

        # Only write impact and remedation if not in a skippable status
        if results['recommendation'] not in config['skip_statuses']:
            ac_verbiage = {}

            if ('acceptance_criteria' in metadata and
                results['recommendation'] in metadata['acceptance_criteria']):

                
                for status in metadata['acceptance_criteria'][results['recommendation']]:
                    if status['id'] == results['acceptance_criteria_id']:
                        ac_verbiage = status


                #TODO ADD CHECK TO VALIDATE FOR AC TO HAVE A STATUS DESCRIPTOR
                output += f"""*Matching Condition*

{ac_verbiage['condition_description']}

"""
                output += f"""*Impact and Risk*
"""
                if 'impact_risk_text' in ac_verbiage:
                    output += f"""
{ac_verbiage['impact_risk_text']}

"""
                    if results['impact_risk_additional_text'] != "":
                        output += f"""*Additional Consultant Comments Impact and Risk*
"""
                output += f"""
{results['impact_risk_additional_text']}

"""

                output += f"""*Remediation Advise*
"""
                if 'remediation_text' in ac_verbiage:
                    output += f"""
{ac_verbiage['remediation_text']}

"""
                    if results['remediation_additional_text'] != "":
                        output += f"""*Additional Consultant Comments for Remediation*
"""
                output += f"""
{results['remediation_additional_text']}

"""


        if results['additional_comments_text'] != "":
            output += f"""*Additional Comments*

{results['additional_comments_text']}

"""

        if len(metadata['references']) > 0:
            output += """*Reference Link(s)*

"""
            for ref in metadata['references']:
                output += f"* {ref['url']}[{ref['title']}]\n"

            output += "\n"


    return output

def __generate_summary_row(item: dict, config: dict) -> str:
    "Generate an AsciiDoc Summary Table Row"

    if item['version'] == 'v0':
        return __generate_summary_row_v0(item, config)
    if item['version'] == 'v1':
        return __generate_summary_row_v1(item, config)


def __generate_summary_row_v0(item: dict, config: dict) -> str:
    "Generate an AsciiDoc Summary Table Row for item file v0"

    output = f"""
// ------------------------ITEM START
// ----ITEM SOURCE:  {item['filename']}

// Category
|
{{set:cellbgcolor!}}
{config['categories'][item['metadata']['category_key']]['short_text']}

// Item Evaluated
a|
"""
    if __will_item_generate_detail(item, config):
        output += f"""<<{item['metadata']['item_evaluated']}>>"""
    else:
        output += f"""{item['metadata']['item_evaluated']}"""

    output += f"""

// Result
| 
{item['results']['result_text']}

// Recommendation
| 
{{set:cellbgcolor:{config['statuses'][item['results']['recommendation']]['color']}}}
{config['statuses'][item['results']['recommendation']]['text']}

// ------------------------ITEM END
"""

    return output

def __generate_summary_row_v1(item: dict, config: dict) -> str:
    "Generate an AsciiDoc Summary Table Row for item file v1"

    output = f"""
// ------------------------ITEM START
// ----ITEM SOURCE:  {item['filename']}

// Category
|
{{set:cellbgcolor!}}
{config['categories'][item['metadata']['category_key']]['short_text']}

// Item Evaluated
a|
"""
    if __will_item_generate_detail(item, config):
        output += f"""<<{item['metadata']['item_evaluated']}>>"""
    else:
        output += f"""{item['metadata']['item_evaluated']}"""
    
    output += f"""

// Result
| 
{item['results']['result_short_text']}

// Recommendation
| 
{{set:cellbgcolor:{config['statuses'][item['results']['recommendation']]['color']}}}
{config['statuses'][item['results']['recommendation']]['text']}

// ------------------------ITEM END
"""

    return output

def __is_item_valid(item: dict, config: dict):
    "Validate a loaded item file this assumes it passes regular YAML validation"

    message: str = ""
    if 'version' in item:
        if item['version'] == 'v0' or item['version'] == 'v1':
            try:
                if item["results"]["recommendation"] not in config["statuses"].keys():
                    message = f"""Invalid recommendation value: '{item['results']['recommendation']}'"""

                if item["metadata"]["category_key"] not in config["categories"].keys():
                    message = f"""Invalid category value:  '{item['metadata']['category_key']}'"""

            except KeyError as e:
                message = f"""Missing key: {e}"""

            if message != "":
                return False, message


        if item['version'] == 'v1':
            if ('acceptance_criteria_id' in item['results'] and 
                item['results']['acceptance_criteria_id'] != ""):
                
                matching_dict: dict = None
                matching_id: str = item['results']['acceptance_criteria_id']

                for status in item['metadata']['acceptance_criteria'][item['results']['recommendation']]:
                    if status['id'] == matching_id:
                        matching_dict = status

                if matching_dict is None:
                    message = f"""acceptance_criteria_id does not exist:  '{item['results']['acceptance_criteria_id']}'"""
            if message != "":
                return False, message


        if message != "":
            return False, message
        else:
            return True, "" 
    else:
        return False, "Unknown item version"

def __load_config(input_dir: str) -> dict:
    "Load config and categories settings"

    config_file: str = path.join(input_dir, "config.yaml")
    categories_file: str = path.join(input_dir, "categories.yaml")

    # Load config
    try:
        with open(config_file) as f:
            config: dict = yaml.safe_load(f)
    except FileNotFoundError:
        # Set default config
        config: dict = {
            "statuses": {
                "changes_required": {
                    "color": "#FF0000",
                    "text": "Changes Required",
                    "description": "Indicates Changes Required for system stability, subscription compliance, or other reason.", # pylint: disable=line-too-long
                },
                "changes_recommended": {
                    "color": "#FEFE20",
                    "text": "Changes Recommended",
                    "description": "Indicates Changes Recommended to align with recommended practices, but not urgently required.", # pylint: disable=line-too-long
                },
                "not_applicable": {
                    "color": "#A6B9BF",
                    "text": "N/A",
                    "description": "No advise given on line item.  For line items which are data-only to provide context.", # pylint: disable=line-too-long
                },
                "advisory": {
                    "color": "#80E5FF",
                    "text": "Advisory",
                    "description": "No change required or recommended, but additional information provided.", # pylint: disable=line-too-long
                },
                "no_change": {
                    "color": "#00FF00",
                    "text": "No Change",
                    "description": "No change required.  In alignment with recommended practices.",
                },
                "tbe": {
                    "color": "#FFFFFF",
                    "text": "To Be Evaluated",
                    "description": "Not yet evaluated.  Will appear only in draft copies.",
                },
            },
            "skip_statuses": ["not_applicable", "tbe", "no_change"]
        }

    # Load categories
    try:
        with open(categories_file) as f:
            config["categories"] = yaml.safe_load(f)["categories"]
    except FileNotFoundError:
        print(f"No categories file found at {categories_file}", file=sys.stderr)
        sys.exit(1)

    return config



def __load_items(input_dir: str, config: dict) -> dict:
    "Load healthcheck items"

    items: dict = {}
    load_errors: int = 0
    item_files: list[str] = [path.join(input_dir, f)
                  for f in listdir(input_dir)
                  if f.endswith('.item')]

    for item_file in item_files:
        print(f"""Loading '{item_file}'""")
        try: 
            with open(item_file) as f:
                item: dict = yaml.safe_load(f)

                is_valid, message = __is_item_valid(item, config)

                if is_valid is not True:
                    load_errors += 1
                    print(f"""File Validation Error:
                    {message} in file '{item_file}'""", file=sys.stderr)
                    continue

                item["filename"] = item_file


        except yaml.parser.ParserError as e:
            load_errors += 1
            print(f"""YAML Parse Error:
            {e} in file '{item}'""", file=sys.stderr)
            continue

        items.setdefault(item["metadata"]["category_key"], []).append(item)

    if load_errors > 0:
        print(f"There were {load_errors} loading errors", file=sys.stderr)
        # sys.exit(1)

    return items

def __load_healthcheck(input_dir: str) -> Tuple[dict, dict]:
    "Load Healthcheck Items and Config"

    config: dict = __load_config(input_dir)
    items: dict = __load_items(input_dir, config)

    return items, config

@click.group()
def cli():
    pass


# click.Path(exists=False, file_okay=True, dir_okay=True, writable=False, readable=True, resolve_path=False, allow_dash=False, path_type=None)

@cli.command()
@click.option('--input-dir', default="./content/healthcheck-items/", show_default=True, type=click.Path(exists=True, file_okay=False))
@click.option('--output-file', default="./content/healthcheck-body.adoc", show_default=True, type=click.Path(dir_okay=False))
def asciidoc(input_dir: str, output_file: str):
    "Generate Healthcheck  AsciiDoc"

    click.echo(f"Generating AsciiDoc {output_file}")

    items, config = __load_healthcheck(input_dir)

    adoc: str = __generate_asciidoc(items, config)

    with open(output_file, "w") as f:
         f.write(adoc)

    click.echo("Completed")

@cli.command()
@click.option('--input-dir', default="./content/healthcheck-items/", show_default=True, type=click.Path(exists=True, file_okay=False))
@click.option('--output-file', default="./content/healthcheck.csv", show_default=True, type=click.Path(dir_okay=False))
def csv(input_dir: str, output_file: str):
    "Generate healthcheck csv"

    # TODO
    click.echo("TODO: Not yet implemented")

    # Example implementation
    # typer.echo(f"Generating csv {output_file}")

    # items, config = __load_healthcheck(input_dir)
    # csv: str = __generate_csv(items, config)

    # with open(output_file, "w") as f:
    #     f.write(csv)

    # typer.echo("Completed")

@cli.command()
@click.argument('dirname', type=click.Path(exists=True, file_okay=False))
def validate_dir(dirname: str):
    "Validate a directory of item files"

    # TODO
    click.echo("TODO: Not yet implemented")

    # Example implementation
    # typer.echo(f"Generating csv {output_file}")

    # items, config = __load_healthcheck(input_dir)
    # csv: str = __generate_csv(items, config)

    # with open(output_file, "w") as f:
    #     f.write(csv)

    # typer.echo("Completed")


@cli.command()
@click.argument('filename', type=click.Path(exists=True, dir_okay=False))
def validate_item(filename: str):
    "Validate a single item file"

    # TODO
    click.echo("TODO: Not yet implemented")

    # Example implementation
    # typer.echo(f"Generating csv {output_file}")

    # items, config = __load_healthcheck(input_dir)
    # csv: str = __generate_csv(items, config)

    # with open(output_file, "w") as f:
    #     f.write(csv)

    # typer.echo("Completed")

if __name__ == "__main__":
    cli()
