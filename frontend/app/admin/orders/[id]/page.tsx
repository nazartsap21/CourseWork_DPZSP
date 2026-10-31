import { AdminOrderView } from "@/components/admin/admin-order-view";

export default async function AdminOrderPage(props: PageProps<"/admin/orders/[id]">) {
  const { id } = await props.params;
  return <AdminOrderView orderId={Number(id)} />;
}
