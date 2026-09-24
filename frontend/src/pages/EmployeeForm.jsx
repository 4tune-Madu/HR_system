import React from 'react';
import {Link} from 'react-router-dom';

export default function EmployeeForm() {
  return <div><Link className="back" to="/employees">Back to employees</Link><div className="page-heading"><div><span className="eyebrow">Employees</span><h2>Employee form</h2><p>Employee creation and editing will be enabled with the complete employee form.</p></div></div><div className="panel notice"><p>The employee API is available, but this form is not yet restored on the current branch.</p></div></div>;
}
