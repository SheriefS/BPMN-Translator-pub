import xml.etree.ElementTree as ET
import csv
import re
from pathlib import Path

def parse_bpmn_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

    tasks = {}
    flows = []
    lanes = {}

    for lane in root.findall('.//bpmn:lane', ns):
        lane_id = lane.attrib.get('id', '')
        lane_name = lane.attrib.get('name', '')
        for flow_node in lane.findall('.//bpmn:flowNodeRef', ns):
            lanes[flow_node.text] = lane_name

    for process in root.findall('bpmn:process', ns):
        for elem in process:
            element_id = elem.attrib.get('id', '')
            element_type = elem.tag.split('}')[-1]
            name = elem.attrib.get('name', '')

            if element_type in ['startEvent', 'endEvent', 'task', 'manualTask', 'sendTask', 'exclusiveGateway', 
                                'callActivity', 'intermediateThrowEvent', 'scriptTask', 'subProcess', 'userTask']:
                print(f"Parsing Task: {name} (Type: {element_type}, ID: {element_id})")
                tasks[element_id] = {
                    'Task Order': None,
                    'Task Name': name,
                    'Task Type': element_type,
                    'Task Dependency': None,
                    'Task Output': None,
                    'Task Outgoing': None,
                    'Responsible for Action': lanes.get(element_id),
                    'Parent Subprocess': None
                }

            if element_type == 'sequenceFlow':
                source_ref = elem.attrib.get('sourceRef', '')
                target_ref = elem.attrib.get('targetRef', '')
                # print(f"Parsing Flow: {source_ref} -> {target_ref}")
                flows.append((source_ref, target_ref))

            if element_type == 'subProcess':
                # print(f"Parsing Subprocess: {name} (ID: {element_id})")
                sub_tasks, sub_flows = parse_subprocess(elem, ns, lanes, element_id)
                tasks.update(sub_tasks)
                flows.extend(sub_flows)

    return tasks, flows

def parse_subprocess(subprocess_elem, ns, lanes, parent_id):
    sub_tasks = {}
    sub_flows = []
    parent_lane = lanes.get(parent_id)
    
    for elem in subprocess_elem:
        element_id = elem.attrib.get('id', '')
        element_type = elem.tag.split('}')[-1]
        name = elem.attrib.get('name', '')

        if element_type in ['startEvent', 'endEvent', 'task', 'manualTask', 'sendTask', 'exclusiveGateway', 
                            'callActivity', 'intermediateThrowEvent', 'scriptTask', 'userTask']:
            print(f"Parsing Subprocess Task: {name} (Type: {element_type}, ID: {element_id}, Parent: {parent_id})")
            sub_tasks[element_id] = {
                'Task Order': None,
                'Task Name': name,
                'Task Type': element_type,
                'Task Dependency': None,
                'Task Output': None,
                'Task Outgoing': None,
                'Responsible for Action': lanes.get(element_id, parent_lane),
                'Parent Subprocess': parent_id  # Tag with parent subprocess ID
            }

        if element_type == 'sequenceFlow':
            source_ref = elem.attrib.get('sourceRef', '')
            target_ref = elem.attrib.get('targetRef', '')
            # print(f"Parsing Subprocess Flow: {source_ref} -> {target_ref}")
            sub_flows.append((source_ref, target_ref))

    return sub_tasks, sub_flows

def determine_sequence(tasks, flows):
    print("Starting task sequence determination...")
    task_order = 1
    visited = set()  # To track visited tasks
    task_stack = []  # Stack to manage tasks while handling divergent paths

    # Find the start event to begin the sequence
    start_event = next((task_id for task_id, task in tasks.items() if task['Task Type'] == 'startEvent' and task['Parent Subprocess'] is None), None)

    if start_event:
        print(f"Starting with: {tasks[start_event]['Task Name']} (ID: {start_event})")
        tasks[start_event]['Task Order'] = task_order
        task_order += 1
        task_stack.append(start_event)
        visited.add(start_event)

    # First Pass: Assign task orders
    while task_stack:
        current_task = task_stack.pop()
        outgoing_flows = [flow for flow in flows if flow[0] == current_task]

        print(f"Processing Task: {tasks[current_task]['Task Name']} (ID: {current_task}) with Outgoing Flows: {outgoing_flows}")



        if tasks[current_task]['Task Type'] == 'exclusiveGateway' and len(outgoing_flows) > 1:
            print(f"Handling diverging exclusiveGateway: {tasks[current_task]['Task Name']}")

            base_order = tasks[current_task]['Task Order']

            for index, (_, target) in enumerate(outgoing_flows):
                if target in tasks and target not in visited:
                    # Check if this path loops back to an earlier task
                    if tasks[target]['Task Order'] is None and any(
                        flow[0] == target and tasks[flow[1]]['Task Order'] is not None and tasks[flow[1]]['Task Order'] < base_order
                        for flow in flows):
                        # Assign a decimal order for the loop-back path
                        sub_task_order = base_order + 0.1
                        tasks[target]['Task Order'] = sub_task_order
                        visited.add(target)
                        task_stack.append(target)
                        print(f"Assigned Sub-Task Order: {tasks[target]['Task Order']} to Task: {tasks[target]['Task Name']}")
                    else:
                        # Assign the next integer task order for the forward-moving path
                        tasks[target]['Task Order'] = task_order
                        visited.add(target)
                        task_stack.append(target)
                        task_order += 1
                        print(f"Assigned Task Order: {tasks[target]['Task Order']} to Task: {tasks[target]['Task Name']}")

        else:
            # Handle standard flow
            for _, target in outgoing_flows:
                if target in tasks and target not in visited:
                    print(f"Assigning Task Order: {task_order} to Task: {tasks[target]['Task Name']} (ID: {target})")
                    if tasks[current_task]['Task Type'] == 'subProcess':
                        temp_order = task_order
                        print(task_order)
                        print(f"Entering subprocess: {tasks[current_task]['Task Name']} (ID: {current_task})")
                        sub_order = assign_subprocess_order(tasks, flows, current_task, task_order, visited)
                        task_order = temp_order
                    tasks[target]['Task Order'] = task_order
                    visited.add(target)
                    task_stack.append(target)
                    task_order += 1

    # Second Pass: Populate Task Dependency and Task Outgoing columns
    for task_id, task in tasks.items():
        incoming_flows = [flow for flow in flows if flow[1] == task_id]
        outgoing_flows = [flow for flow in flows if flow[0] == task_id]

        # Populate the Task Dependency column
        dependencies = []
        for source, _ in incoming_flows:
            if source in tasks and tasks[source]['Task Order'] is not None:
                task_name = tasks[source]['Task Name'] if tasks[source]['Task Name'] else "None"
                dependencies.append(f"{task_name} ({tasks[source]['Task Order']})")
        tasks[task_id]['Task Dependency'] = ", ".join(dependencies) if dependencies else "None"

        # Populate the Task Outgoing column
        outgoing_list = []
        for _, target in outgoing_flows:
            if target in tasks and tasks[target]['Task Order'] is not None:
                task_name = tasks[target]['Task Name'] if tasks[target]['Task Name'] else "None"
                outgoing_list.append(f"{task_name} ({tasks[target]['Task Order']})")
        tasks[task_id]['Task Outgoing'] = ", ".join(outgoing_list) if outgoing_list else "None"

    return tasks

def assign_subprocess_order(tasks, flows, subprocess_id, base_order, visited):
    base_order = base_order - 1
    sub_task_order = 0
    task_stack = []

    # Filter tasks and flows specifically within the subprocess
    subprocess_tasks = {task_id: task for task_id, task in tasks.items() if task['Parent Subprocess'] == subprocess_id}
    subprocess_flows = [flow for flow in flows if flow[0] in subprocess_tasks and flow[1] in subprocess_tasks]

    # Find the start event within the subprocess
    sub_start_event = next((task_id for task_id, task in subprocess_tasks.items() if task['Task Type'] == 'startEvent'), None)

    if sub_start_event:
        sub_task_order += 1  # Increment for the base order within subprocess
        tasks[sub_start_event]['Task Order'] = f"{base_order}[{sub_task_order}]"
        task_stack.append(sub_start_event)
        visited.add(sub_start_event)
        print(f"Subprocess Start Event: {tasks[sub_start_event]['Task Name']} assigned order {tasks[sub_start_event]['Task Order']}")

    # Process all tasks within the subprocess
    while task_stack:
        current_task = task_stack.pop()
        outgoing_flows = [flow for flow in subprocess_flows if flow[0] == current_task]

        if tasks[current_task]['Task Type'] == 'exclusiveGateway' and len(outgoing_flows) > 1:
            print(f"Handling diverging exclusiveGateway within subprocess: {tasks[current_task]['Task Name']}")

            base_order_str = tasks[current_task]['Task Order']
            base_order_int = int(base_order_str.split('[')[1].split(']')[0])

            for index, (_, target) in enumerate(outgoing_flows):
                if target in subprocess_tasks and target not in visited:
                    # Check if this path loops back to an earlier task
                    if tasks[target]['Task Order'] is None and any(
                        flow[0] == target and tasks[flow[1]]['Task Order'] is not None and tasks[flow[1]]['Task Order'] < base_order_str
                        for flow in subprocess_flows):
                        # Assign a loop-back order with decimal notation
                        loop_back_order = f"{base_order}[{base_order_int}.{index}]"
                        tasks[target]['Task Order'] = loop_back_order
                        visited.add(target)
                        task_stack.append(target)
                        print(f"Assigned Loop-back Task Order {loop_back_order} to Task: {tasks[target]['Task Name']}")
                    else:
                        # Assign the next order for the forward-moving path
                        sub_task_order += 1
                        forward_order = f"{base_order}[{sub_task_order}]"
                        tasks[target]['Task Order'] = forward_order
                        visited.add(target)
                        task_stack.append(target)
                        print(f"Assigned Task Order {forward_order} to Task: {tasks[target]['Task Name']}")

        else:
            # Handle standard flow
            for _, target in outgoing_flows:
                if target in subprocess_tasks and target not in visited:
                    sub_task_order += 1
                    tasks[target]['Task Order'] = f"{base_order}[{sub_task_order}]"
                    visited.add(target)
                    task_stack.append(target)
                    print(f"Assigned Subprocess Task Order: {tasks[target]['Task Order']} to Task: {tasks[target]['Task Name']}")

    return f"{base_order}[{sub_task_order}]"

def sort_key(task_order):
    match = re.match(r"(\d+)(\[(\d+)(\.\d+)?\])?", str(task_order))
    if match:
        main_order = int(match.group(1))
        sub_order = int(match.group(3)) if match.group(3) else 0
        decimal_order = float(match.group(4)) if match.group(4) else 0.0
        return (main_order, sub_order, decimal_order)
    return (float('inf'),)

def write_to_csv(tasks, output_csv):
    fieldnames = ['Task Order', 'Task Name', 'Task Type', 'Task Dependency', 'Task Output', 'Task Outgoing', 'Responsible for Action']
    
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Updated sorting logic to handle NoneType for 'Task Order'
        sorted_tasks = sorted(tasks.items(), key=lambda k: (k[1]['Task Order'] is None, sort_key(k[1]['Task Order']) if k[1]['Task Order'] is not None else (float('inf'),)))
        
        for _, task_info in sorted_tasks:
            # Exclude the 'Parent Subprocess' field before writing to CSV
            task_info = {key: value for key, value in task_info.items() if key in fieldnames}
            writer.writerow(task_info)

# Main function to run the conversion
def convert_bpmn_to_csv(xml_file, output_csv):
    tasks, flows = parse_bpmn_xml(xml_file)
    tasks = determine_sequence(tasks, flows)
    write_to_csv(tasks, output_csv)
    print(f"Conversion completed. CSV saved to {output_csv}")

# Example usage
if __name__ == "__main__":
    # Get the current script directory
    script_dir = Path(__file__).parent
    
    # Define the relative path to the BPMN file and output CSV
    xml_file = script_dir / 'BPMN_Files' / 'complicated that has glitches.bpmn'  # Replace 'your_bpmn_file.bpmn' with your actual BPMN file name
    output_csv = script_dir / 'CSV_Output' / 'output3.csv'

    
    convert_bpmn_to_csv(xml_file, output_csv)

        # Define the relative path to the BPMN file and output CSV
    xml_file = script_dir / 'BPMN_Files' / 'simple that works.bpmn'  # Replace 'your_bpmn_file.bpmn' with your actual BPMN file name
    output_csv = script_dir / 'CSV_Output' / 'output2.csv'

    
    convert_bpmn_to_csv(xml_file, output_csv)