import { Component, input } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { ReportTable as ReportTableData } from '../../../api/evaluations.service';
import { plainText } from './plain-text';

/** Un tableau d'un rapport : les colonnes viennent des en-têtes du rapport lui-même. */
@Component({
  selector: 'app-report-table',
  imports: [MatTableModule],
  templateUrl: './report-table.html',
  styleUrl: './report-table.scss',
})
export class ReportTable {
  readonly table = input.required<ReportTableData>();
  readonly label = input.required<string>();

  readonly plainText = plainText;

  columns(): string[] {
    return this.table().headers.map((_, index) => `c${index}`);
  }
}
