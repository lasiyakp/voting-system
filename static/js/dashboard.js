// Render candidate-wise vote chart on user dashboard
const chartDataNode = document.getElementById('chart-data');
if (chartDataNode) {
  const payload = JSON.parse(chartDataNode.textContent);
  const ctx = document.getElementById('voteChart');

  if (ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: payload.labels,
        datasets: [{
          label: 'Votes',
          data: payload.counts,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        }
      }
    });
  }
}
