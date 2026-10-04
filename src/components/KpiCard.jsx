function KpiCard({ title, value, change }) {

  return (
    <div className="kpi-card">

      <h3>{title}</h3>

      <h2>{value}</h2>

      <p className="kpi-change">
        {change}
      </p>

    </div>
  );
}

export default KpiCard;