import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  Badge,
  Card,
  Textarea,
  Select,
  Checkbox,
  Dialog,
  Tooltip,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
  Skeleton,
  Alert,
} from "@/components/ui";

describe("Component Contracts", () => {
  describe("Badge", () => {
    it("renders text and applies variant", () => {
      render(<Badge variant="success">Verified</Badge>);
      const badge = screen.getByText("Verified");
      expect(badge).toBeInTheDocument();
      expect(badge.className).toContain("bg-green-100");
    });
  });

  describe("Card", () => {
    it("renders children with surface styling", () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText("Card content")).toBeInTheDocument();
    });

    it("applies interactive variant styling", () => {
      const { container } = render(
        <Card variant="interactive">Interactive card</Card>
      );
      expect(container.firstChild).toHaveClass("cursor-pointer");
    });
  });

  describe("Textarea", () => {
    it("renders an accessible textarea", () => {
      render(
        <label>
          Notes
          <Textarea name="notes" />
        </label>
      );
      expect(
        screen.getByRole("textbox", { name: "Notes" })
      ).toBeInTheDocument();
    });

    it("exposes invalid and disabled attributes", () => {
      render(<Textarea aria-label="Description" invalid disabled />);
      const el = screen.getByRole("textbox", { name: "Description" });
      expect(el).toHaveAttribute("aria-invalid", "true");
      expect(el).toBeDisabled();
    });
  });

  describe("Select", () => {
    it("renders select with options and handles value change", () => {
      render(
        <label>
          Filter
          <Select name="filter" defaultValue="a">
            <option value="a">Option A</option>
            <option value="b">Option B</option>
          </Select>
        </label>
      );
      const select = screen.getByRole("combobox", { name: "Filter" });
      expect(select).toBeInTheDocument();
      fireEvent.change(select, { target: { value: "b" } });
      expect(select).toHaveValue("b");
    });
  });

  describe("Checkbox", () => {
    it("renders with associated label and toggles checked state", () => {
      render(<Checkbox label="Accept terms" />);
      const checkbox = screen.getByRole("checkbox", { name: "Accept terms" });
      expect(checkbox).not.toBeChecked();
      fireEvent.click(checkbox);
      expect(checkbox).toBeChecked();
    });
  });

  describe("Dialog", () => {
    it("does not render when closed", () => {
      render(
        <Dialog open={false} onClose={() => {}} title="Test Dialog">
          Body
        </Dialog>
      );
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("renders title, description, and closes on Escape", () => {
      const onClose = vi.fn();
      render(
        <Dialog
          open={true}
          onClose={onClose}
          title="Confirm Ingestion"
          description="Are you sure you want to index?"
        >
          Dialog body
        </Dialog>
      );
      expect(
        screen.getByRole("dialog", { name: "Confirm Ingestion" })
      ).toBeInTheDocument();
      expect(
        screen.getByText("Are you sure you want to index?")
      ).toBeInTheDocument();

      fireEvent.keyDown(document, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("Tooltip", () => {
    it("displays tooltip on hover/focus", () => {
      render(
        <Tooltip content="Help information">
          <button type="button">Hover me</button>
        </Tooltip>
      );
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

      fireEvent.mouseEnter(screen.getByRole("button", { name: "Hover me" }));
      expect(screen.getByRole("tooltip")).toHaveTextContent("Help information");
    });
  });

  describe("Table", () => {
    it("renders responsive structured table with header, rows, and caption", () => {
      render(
        <Table>
          <TableCaption>Document List</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Filename</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>report.pdf</TableCell>
              <TableCell>Indexed</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole("table")).toBeInTheDocument();
      expect(screen.getByText("Document List")).toBeInTheDocument();
      expect(screen.getByText("report.pdf")).toBeInTheDocument();
      expect(screen.getByText("Indexed")).toBeInTheDocument();
    });
  });

  describe("Skeleton", () => {
    it("renders loading placeholder with accessibility attributes", () => {
      render(<Skeleton variant="card" data-testid="card-skeleton" />);
      const el = screen.getByTestId("card-skeleton");
      expect(el).toHaveAttribute("aria-busy", "true");
      expect(el).toHaveAttribute("aria-hidden", "true");
    });
  });

  describe("Alert", () => {
    it("renders danger alert with role='alert'", () => {
      render(
        <Alert variant="danger" title="Engine failure">
          Could not extract vector geometry.
        </Alert>
      );
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(screen.getByText("Engine failure")).toBeInTheDocument();
      expect(
        screen.getByText("Could not extract vector geometry.")
      ).toBeInTheDocument();
    });

    it("renders info alert with role='status'", () => {
      render(
        <Alert variant="info" title="Indexing queued">
          Your document will process shortly.
        </Alert>
      );
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });
});
