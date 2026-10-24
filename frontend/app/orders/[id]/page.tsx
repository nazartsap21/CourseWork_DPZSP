import { OrderView } from "@/components/orders/order-view";

export default async function OrderPage(props: PageProps<"/orders/[id]">) {
  const { id } = await props.params;
  return <OrderView orderId={Number(id)} />;
}
