document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM loaded!");
  const checkbox = document.getElementById('led-switch') as HTMLInputElement;
  const led = document.getElementById('led') as HTMLElement;

  if (!checkbox || !led) {
    console.error('Missing LED or switch element!');
    return;
  }

  checkbox.addEventListener('change', async () => {
    try {
      const res = await fetch('/toggle', { method: 'POST' });
      if (!res.ok) throw new Error('Network response was not ok');

      const data: { led_on: boolean } = await res.json();
      led.className = 'led ' + (data.led_on ? 'on' : 'off');
      checkbox.checked = data.led_on;
    } catch (err) {
      console.error('Failed to toggle LED:', err);
    }
  });
});