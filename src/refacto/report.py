import json
import math
import os

def format_and_write_report(base, report_entries, grand_total, total_tax_collected):
    output_lines = []
    json_data = []

    for entry in report_entries:
        output_lines.extend(entry['lines'])
        json_data.append(entry['json'])

    output_lines.append(f'Grand Total: {grand_total:.2f} EUR')
    output_lines.append(f'Total Tax Collected: {total_tax_collected:.2f} EUR')

    result = '\n'.join(output_lines)
    print(result)

    with open(os.path.join(base, 'output.json'), 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    return result
