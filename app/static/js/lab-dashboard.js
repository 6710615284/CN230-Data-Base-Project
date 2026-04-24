document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('labQueueTable');
  const filter = document.getElementById('queueFilter');
  const sort = document.getElementById('queueSort');
  if (!table || !filter || !sort) return;

  const tbody = table.querySelector('tbody');
  const originalRows = Array.from(tbody.querySelectorAll('tr'));

  function applyFilterAndSort() {
    let rows = [...originalRows];

    const filterValue = filter.value;
    if (filterValue !== 'all') {
      rows = rows.filter(row => row.dataset.priority === filterValue);
    }

    const sortValue = sort.value;
    if (sortValue === 'default') {
      rows.sort((a, b) => {
        const orderA = Number(a.dataset.orderId || a.children[0].innerText.trim());
        const orderB = Number(b.dataset.orderId || b.children[0].innerText.trim());
        return orderA - orderB;
      });
    } else if (sortValue === 'urgent-first') {
      rows.sort((a, b) => {
        const pa = a.dataset.priority === 'urgent' ? 1 : 0;
        const pb = b.dataset.priority === 'urgent' ? 1 : 0;
        return pb - pa;
      });
    } else if (sortValue === 'latest') {
      rows.sort((a, b) => {
        return new Date(b.dataset.ordered || 0) - new Date(a.dataset.ordered || 0);
      });
    } else if (sortValue === 'pending-high') {
      rows.sort((a, b) => Number(b.dataset.pending || 0) - Number(a.dataset.pending || 0));
    }

    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
  }

  filter.addEventListener('change', applyFilterAndSort);
  sort.addEventListener('change', applyFilterAndSort);
  
  applyFilterAndSort();
});