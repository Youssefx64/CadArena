import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Alert from './Alert';

describe('Alert Component', () => {
  it('renders alert with title and message', () => {
    render(<Alert type="info" title="Info" message="This is an info alert" />);
    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText('This is an info alert')).toBeInTheDocument();
  });

  it('renders success alert', () => {
    const { container } = render(
      <Alert type="success" title="Success" message="Operation completed" />
    );
    expect(container.querySelector('[role="alert"]')).toBeInTheDocument();
  });

  it('renders error alert', () => {
    const { container } = render(
      <Alert type="error" title="Error" message="Something went wrong" />
    );
    expect(container.querySelector('[role="alert"]')).toBeInTheDocument();
  });

  it('renders warning alert', () => {
    const { container } = render(
      <Alert type="warning" title="Warning" message="Please be careful" />
    );
    expect(container.querySelector('[role="alert"]')).toBeInTheDocument();
  });

  it('handles dismiss button click', async () => {
    const handleDismiss = jest.fn();
    render(
      <Alert
        type="info"
        title="Info"
        message="This is an info alert"
        dismissible
        onDismiss={handleDismiss}
      />
    );

    const dismissButton = screen.getByLabelText('Dismiss alert');
    await userEvent.click(dismissButton);

    expect(handleDismiss).toHaveBeenCalled();
  });

  it('does not show dismiss button when dismissible is false', () => {
    render(
      <Alert
        type="info"
        title="Info"
        message="This is an info alert"
        dismissible={false}
      />
    );

    expect(screen.queryByLabelText('Dismiss alert')).not.toBeInTheDocument();
  });

  it('has correct aria-live attribute', () => {
    const { container } = render(
      <Alert type="info" title="Info" message="This is an info alert" />
    );

    const alert = container.querySelector('[role="alert"]');
    expect(alert).toHaveAttribute('aria-live', 'polite');
  });
});
