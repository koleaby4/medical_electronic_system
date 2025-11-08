document.addEventListener('DOMContentLoaded', () => {
  const list = document.getElementById('patients');
  const form = document.getElementById('patient-form');

  async function loadPatients() {
    list.innerHTML = 'Loading...';
    try {
      const res = await fetch('/patients');
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      list.innerHTML = '';
      for (const p of data) {
        const li = document.createElement('li');
        li.textContent = `${p.name} — ${p.dob} ${p.notes ? '- ' + p.notes : ''}`;
        list.appendChild(li);
      }
    } catch (err) {
      list.innerHTML = 'Error loading patients';
      console.error(err);
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    const res = await fetch('/patients', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      form.reset();
      loadPatients();
    } else {
      alert('Failed to add patient');
    }
  });

  loadPatients();
});